$(document).ready(function () {
  /* VARIABLES */

  const dlgArmarSlide = new bootstrap.Modal(
    document.getElementById("dlgArmarSlide")
  );

  $("#entryformSel").select2();

  const selectCase = $("#selectCase");
  const selectUnit = $("#selectUnit");
  const selectCassette = $("#selectCassette");
  const selectStain = $("#selectStain");

  selectStain.select2();

  // Main table which displays all availables Cases to build Slides from.
  const tableIndex = $(".zero-configuration").DataTable({
    ajax: {
      url: Urls["lab:slide_build"](),
      contentType: "application/json",
      type: "GET",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
      },
      data: () => {
        return {
          range: $("#entryformSel").val(),
          no_caso: $("#noCaso").val(),
        };
      },
      dataSrc: "",
    },
    columns: [
      {
        data: "case.no_caso",
        name: "case",
        type: "string",
        title: "Caso",
      },
      {
        data: "identification",
        name: "identification",
        type: "string",
        title: "Identificacion",
        render: (data) => {
          return `${data.cage} ${data.group} ${data.extra_features_detail}`;
        },
      },
      {
        data: "unit.correlative",
        name: "unitCorrelative",
        type: "num",
        title: "# Unidad",
      },
      {
        data: "cassette.correlative",
        name: "cassetteCorrelative",
        type: "num",
        title: "# Cassette",
        render: (data) => {
          if (data) {
            return `${data}`;
          } else {
            return "N/A";
          }
        },
      },
      {
        data: "cassette.observation",
        name: "cassetteObservation",
        title: "Observacion",
        render: (data) => {
          if (data) {
            return `${data}`;
          } else {
            return "";
          }
        },
      },
      {
        data: "stain_text",
        name: "stain",
        title: "Tinción",
        render: (data) => {
          if (data) {
            return `${data}`;
          } else {
            return "N/A";
          }
        },
      },
      {
        data: "dates_text",
        name: "analysis",
        title: "Ultimo Analisis Ingresado (Tinción)",
        render: (data) => {
          if (data) {
            return `${data}`;
          } else {
            return "S/I";
          }
        },
      },
    ],

    dom: "Bfrtip",

    buttons: [
      {
        text: "Seleccionar todos",
        action: function () {
          tableIndex
            .rows({
              page: "current",
            })
            .select();
        },
      },

      {
        text: "Deseleccionar todos",
        action: function () {
          tableIndex
            .rows({
              page: "current",
            })
            .deselect();
        },
      },
    ],

    select: {
      style: "multi",
    },

    paging: false,

    oLanguage: {
      sUrl: "https://cdn.datatables.net/plug-ins/1.10.16/i18n/Spanish.json",
    },
  });

  const tableBuild = $("#tableBuildDialog").DataTable({
    ajax: {
      url: Urls["lab:slide_prebuild"](),
      contentType: "application/json",
      type: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
      },
      data: function () {
        if (selectedItems && selectedItems.length > 0) {
          return JSON.stringify(
            selectedItems.map((item) => {
              const unit = item.unit.id;
              const cassette = item.cassette ? item.cassette.id : -1;
              return {
                unit,
                cassette,
              };
            })
          );
        }
        return [];
      },
      dataSrc: "",
    },

    columns: [
      {
        data: "case.no_caso",
        name: "case",
        type: "string",
        title: "Caso",
      },
      {
        data: "identification",
        name: "identification",
        type: "num",
        title: "Identificacion",
        render: (data) => {
          return `${data.cage} ${data.group} ${data.extra_features_detail}`;
        },
      },
      {
        data: "unit.correlative",
        name: "unitCorrelative",
        type: "num",
        title: "# Unidad",
      },
      {
        data: "cassette",
        name: "cassetteCorrelative",
        type: "num",
        title: "# Cassette",
        render: (data) => {
          if (data !== undefined && data[0] && data[0].correlative) {
            return `${data[0].correlative}`;
          } else {
            return `N/A`;
          }
        },
      },
      {
        data: "organs",
        name: "organs",
        type: "string",
        title: "Organos",
        orderable: false,
      },
      {
        data: "stain.abbreviation",
        name: "stain",
        type: "string",
        title: "Tincion",
        orderable: false,
      },
      {
        data: "cassette",
        name: "index",
        type: "string",
        title: "Correlativo",
        orderable: false,
        render: (data, type, row) => {
          if (data !== undefined && data[0] && data[0].correlative) {
            return `${row.case.no_caso},${row.stain.abbreviation},${data[0].correlative}`;
          } else {
            return `${row.case.no_caso},${row.stain.abbreviation},${row.unit.correlative}`;
          }
        },
      },
    ],

    rowsGroup: [0],

    orderMulti: false,

    select: {
      style: "multi",
    },

    paging: false,
  });

  // Array of Unit Ids from the index table.
  var selectedItems = [];

  /* END VARIABLES*/

  /* FUNCTIONS */
  function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== "") {
      var cookies = document.cookie.split(";");
      for (var i = 0; i < cookies.length; i++) {
        var cookie = jQuery.trim(cookies[i]);
        // Does this cookie string begin with the name we want?
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  function setSelectedUnits() {
    let selected = [];
    let item = tableIndex
      .rows({ selected: true })
      .data()
      .each((element) => {
        selected.push(element);
      });
    selectedItems = selected;
  }

  function getUnitByPk(pk) {
    const unit = selectedItems.find((item) => item.unit.pk == pk);
    return unit;
  }

  function getCassetteByPk(pk) {
    const cassette = selectedItems.find((item) => item.cassette.pk == pk);
    return cassette;
  }

  function groupBy(xs) {
    return xs.reduce(function (rv, x) {
      (rv[x["case"].fields.no_caso] = rv[x["case"].fields.no_caso] || []).push(
        x
      );
      return rv;
    }, {});
  }

  /* END FUNCTIONS*/

  /* EVENTS */

  tableIndex.on("select.dt deselect.dt", () => {
    setSelectedUnits();
  });

  $(".zero-configuration").on("click", ".detailTrigger", function (e) {
    e.preventDefault();
    const url = $(e.target).attr("href");
    $.get(url, function (data, textStatus) {
      Swal.fire({
        html: data,
        width: "80%",
      });
    });
  });

  $(".btn-close").click(() => {
    dlgArmarSlide.hide();
  });

  $("#btnArmarSlide").click(() => {
    tableBuild.ajax.reload();
    let now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    $("#buildAt").val(now.toISOString().slice(0, 16));

    dlgArmarSlide.show();

    let cases = selectedItems
      .map((item, index) => {
        return {
          id: `${item.case.pk};${item.identification.pk};${item.unit.pk}`,
          text: `${item.case.fields.no_caso} / ${item.identification.fields.cage} / ${item.unit.fields.correlative}`,
        };
      })
      .filter(
        (row, index, self) =>
          index === self.findIndex((obj) => obj.id === row.id)
      );

    cases.unshift({
      id: -1,
      text: "Seleccione un Caso / Identificacion / Unidad",
    });

    selectCase.select2({
      data: cases,
    });
    selectStain.select2();
  });

  $("#btnDeleteSelected").click(() => {
    tableBuild.rows(".selected").remove().draw(false);
  });

  selectCase.on("change", (e) => {
    const pk = e.target.value.split(";")[2];

    if (pk < 0) return;

    const filteredItems = selectedItems.filter(
      (item) => item.unit.pk == pk && item["cassette"] != null
    );

    let cassettes = filteredItems.map((item) => {
      return {
        id: item.cassette.pk,
        text: `${item.cassette.fields.correlative}`,
      };
    });

    cassettes.unshift({
      id: -1,
      text: "Seleccione un Cassette",
    });

    selectCassette.empty();
    for (const cassette of cassettes) {
      selectCassette.append(new Option(cassette.text, cassette.id));
    }

    if (selectCassette.hasClass("select2-hidden-accessible")) {
      selectCassette.select2("destroy");
    }
    selectCassette.select2();
  });

  $("#btnCreateSlide").click(() => {
    const stain = selectStain.select2("data")[0];
    tableBuild
      .rows({ selected: true })
      .data()
      .each((value, index) => {
        let newRow = { ...value };
        newRow.stain = {
          id: parseInt(stain.id),
          abbreviation: stain.text,
        };
        let alreadyExists = false;
        tableBuild
          .rows()
          .data()
          .each((row, index) => {
            // Can't reliably compare 2 javascript objects
            // thus is necessary to transform them into strings
            // and then compare the resulting strings
            // this comparison fails if the properties are not
            // ordered the same in both objects.

            if (JSON.stringify(row) == JSON.stringify(newRow)) {
              alreadyExists = true;
            }
          });

        if (!alreadyExists) {
          tableBuild.row.add(newRow).draw();
        } else {
          Swal.fire({
            title:
              "Ya existe un slide de este Cassette/Unidad con esta tinción",
            icon: "error",
          });
        }
      });
  });

  
  $("#btnSaveSlide").click(() => {
    document.querySelector('#btnSaveSlide').disabled = true;
  });

  $("#btnSaveSlide").click(() => {
    const build_at = $("#buildAt").val();

    let slides = [];
    let text = "";
    const data = tableBuild
      .rows()
      .data()
      .each((value, index) => {
        console.log(value)
        let correlative = value.slide;
        let new_slide = {
          unit_id: value.unit.id,
          stain_id: value.stain.id,
        };
        if (
          value.cassette !== undefined &&
          value.cassette[0] &&
          value.cassette[0].id > 0
        ) {
          let correlative = value.cassette[0].correlative;
          new_slide.cassette_id = value.cassette[0].id;
        }

        new_slide.correlative = correlative;
        slides.push(new_slide);

        const text_abbreviation = value.stain.abbreviation
          .replace(" ", ",")
          .replace("+", ",")
          .toLocaleUpperCase();
        const text_correlative = new String(correlative).padStart(3, "0");

        text += `<li class="list-group-item">${value.case.no_caso},${text_abbreviation},${text_correlative}</li>`;
      });
    
    if (slides.length == 0) {
      Swal.fire({
        icon: "error",
        title: "No hay slides para armar",
      });
      document.querySelector('#btnSaveSlide').disabled = false;
    }else{
      Swal.fire({
        title: "Se crearan los siguientes slides:",
        html: `<ul class="list-group list-group-flush overflow-auto" style="max-height: 18rem;">${text}</ul>`,
      }).then((result) => {
        if (result.isConfirmed) {
          $.ajax(Urls["lab:slide_build"](), {
            data: JSON.stringify({
              build_at: build_at,
              slides: slides,
            }),

            method: "POST",

            headers: {
              "X-CSRFToken": getCookie("csrftoken"),
            },

            contentType: "application/json; charset=utf-8",

            success: (data, textStatus) => {
              Swal.fire({
                icon: "success",
                title: "Guardado",
              });
              location.reload();
            },
            error: (xhr, textStatus, error) => {
              Swal.fire({
                icon: "error",
              });
            },
            always: () => {
              document.querySelector('#btnSaveSlide').disabled = false;
            }
          });
        }else{
          document.querySelector('#btnSaveSlide').disabled = false;
        }
      });
    }
  });

  $("#btnHideSlide").click(() => {
    Swal.fire({
      title: "Los slides seleccionados se marcaran como 'No require armado'.",
      text: "Puede agregar un comentario adicional:",
      input: "text",
      showCancelButton: true,
      cancelButtonText: "Cancelar",
    }).then((result) => {
      if (result.isConfirmed) {
        const message = result.value;
        const slides = selectedItems.map((item) => {
          const unit = item.unit.pk;
          const cassette = item.cassette ? item.cassette.pk : -1;
          return {
            unit,
            cassette,
          };
        });

        $.ajax(Urls["lab:slide_hide"](), {
          data: JSON.stringify({
            message,
            slides,
          }),

          method: "POST",

          headers: {
            "X-CSRFToken": getCookie("csrftoken"),
          },

          contentType: "application/json; charset=utf-8",

          success: (data, textStatus) => {
            Swal.fire({
              icon: "success",
              title: "Guardado",
            });
            location.reload();
          },
          error: (xhr, textStatus, error) => {
            Swal.fire({
              icon: "error",
            });
          },
        });
      }
    });
  });

  $("#btnEntryformFilter").click(() => {
    tableIndex.ajax.reload();
  });

  /* END EVENTS */
});
