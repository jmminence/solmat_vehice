$(document).ready(function () {
  /* VARIABLES */

  const dlgArmarCassette = new bootstrap.Modal(
    document.getElementById("dlgArmarCassette")
  );

  const dlgConfigurarCassette = new bootstrap.Modal(
    document.getElementById("dlgConfigurarCassette"),
    {
      backdrop: "static",
      keyboard: false,
    }
  );

  const alertNonLabProcess = $(".alertNonLab");
  alertNonLabProcess.tooltip({ boundary: "window" });

  const rulesForm = {
    uniqueOrgans: $("#selUniqueOrgans"),
    groupOrgans: $("#selGroupOrgans"),
  };

  var rules = {
    uniques: [],
    groups: [],
    max: 0,
  };

  // organs was defined in the build.html as it was a variable returned from the server
  const organOptions = organs.map((organ) => {
    return {
      id: organ.pk,
      text: organ.fields.name,
    };
  });

  $(".organSelect").select2({
    data: organOptions,
    width: "100%",
    placeholder: "Seleccione organos",
  });

  // Main table which displays all availables Cases to build Cassettes from.
  const tableIndex = $(".zero-configuration").DataTable({
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

    rowsGroup: [2],

    oLanguage: {
      sUrl: "https://cdn.datatables.net/plug-ins/1.10.16/i18n/Spanish.json",
    },
  });

  // Array of Unit Ids from the index table.
  var selectedItems = [];

  // Array of Cassettes from the build table.
  var selectedCassettes = [];

  // Array of Units used in logic for the build form.
  var units = [];

  // Modal table which displays selectedItems's Cassettes.

  const tableBuild = $("#tableBuildDialog").DataTable({
    ajax: {
      url: Urls["lab:cassette_prebuild"](),
      contentType: "application/json",
      type: "POST",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
      },
      data: function () {
        return JSON.stringify({
          selected: selectedItems,
          rules: rules,
        });
      },
      dataSrc: "",
    },

    paging: false,

    columns: [
      {
        data: "case",
        name: "case",
        type: "string",
        title: "Caso",
      },
      {
        data: "identification",
        name: "identification",
        type: "string",
        title: "Identificacion",
      },
      {
        data: "unit",
        name: "unitCorrelative",
        type: "num",
        title: "# Unidad",
      },
      {
        data: "cassette",
        name: "cassetteCorrelative",
        type: "num",
        title: "# Cassette",
      },
      {
        data: "organs",
        name: "cassetteOrgans",
        title: "Organos",
        render: function (data, type, row, meta) {
          return `<span class="unitSelectOrgan flex flex-row" id="${row.unit_id};${row.cassette}"></span>`;
        },
      },
      {
        data: "cassette",
        name: "observations",
        title: "Observaciones",
        render: function (data, type, row, meta) {
          return `<textarea cols="30" rows="3" class="form-control observation"></textarea>`;
        },
      },
    ],

    rowsGroup: [0],

    select: {
      style: "multi",
    },
  });

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

  // Sets the variable selectedItems with the
  // values from the fith column of the table
  // which should be the id unit
  function setSelectedUnits() {
    const ID_COLUMN = 5; // 5 is the column with the id of the unit
    let selected = [];
    let item = tableIndex
      .rows({ selected: true })
      .data()
      .each((element) => {
        selected.push(parseInt(element[ID_COLUMN]));
      });

    selectedItems = selected;
  }

  function setSelectedCassettes() {
    let selected = [];
    let item = tableBuild
      .rows({ selected: true })
      .data()
      .each((element) => {
        selected.push({
          unitId: element.unit_id,
          cassette: element.cassette,
        });
      });

    selectedCassettes = selected;
  }

  // Convert the response received from the server
  // into a format that Select2 can handle
  // then initiate Select2.
  function activateNewCassetteUnitSelect(response) {
    let options = response.map((row) => {
      return {
        id: row.unit_id,
        text: `${row.case} / ${row.identification} / ${row.unit}`,
      };
    });
  }

  function activateOrganSelect() {
    $(".unitSelectOrgan").each(function (i, elem) {
      const element = $(elem);
      const elementId = elem.id.split(";");
      const organs = getOrgansFromUnit(elementId[0]);
      const cassetteOrgans = getOrgansFromCassette(elementId[0], elementId[1]);

      for (const organ of cassetteOrgans) {
        const organDOM = `<div class="btn-group mr-1" role="group">
                            <button class="btn btn-secondary organId" type="button" value="${organ.pk}" disabled>${organ.fields.abbreviation}</button>
                            <button class="btn btn-danger deleteOrgan" type="button">X</button>
                          </div>`;
        element.append(organDOM);
      }
    });
  }

  function getUnitsFromUnitId(unitId) {
    return units.filter((row) => {
      return row.unit_id === parseInt(unitId);
    });
  }

  function getOrgansFromUnit(unitId) {
    const findAvailable = units.find((row) => row.unit_id == unitId);
    return JSON.parse(findAvailable.organs);
  }

  function getOrgansFromCassette(unitId, cassetteId) {
    const findAvailable = units.find(
      (row) => row.unit_id == unitId && row.cassette == cassetteId
    );
    let organs = [];
    try {
      organs = JSON.parse(findAvailable.cassette_organs);
    } catch (SyntaxError) {
      organs = [];
    }
    return organs;
  }

  function updateCorrelativeCassette() {
    let caseId = 1;
    let correlativeNumber = 1;

    tableBuild.rows().every(function (rowIdx, tableLoop, rowLoop) {
      const row = this.data();
      let currentCorrelativeCell = tableBuild.cell({
        row: rowIdx,
        column: 3,
      });

      if (row.case != caseId) {
        caseId = row.case;
        correlativeNumber = row.cassette;
      }
      currentCorrelativeCell.data(correlativeNumber);
      correlativeNumber += 1;
    });
  }

  function checkIfExists(organId) {
    const unique = rules.uniques.includes(organId);
    const group = rules.groups.some((group) => group.includes(organId));
    return unique || group;
  }

  /* END FUNCTIONS*/

  /* EVENTS */

  $("#btnCreateCassette").click(() => {
    const selectedRows = tableBuild
      .rows({ selected: true })
      .data()
      .each((value, index) => {
        const unitList = units.filter((row) => row.unit_id === value.unit_id);
        const cassetteCount = unitList.length + 1;

        const newRow = {
          case: unitList[0].case,
          identification: unitList[0].identification,
          organs: unitList[0].organs,
          unit: unitList[0].unit,
          unit_id: unitList[0].unit_id,
          cassette: cassetteCount,
          cassette_organs: [],
        };

        units.push(newRow);

        tableBuild.row.add(newRow).draw();
      });

    updateCorrelativeCassette();
  });

  $(".btn-close").click(function () {
    dlgArmarCassette.hide();
    dlgConfigurarCassette.hide();
  });

  $("#btnDeleteSelected").click(() => {
    tableBuild.rows(".selected").remove().draw(false);

    units = units.filter((row) => {
      const unitId = row.unit_id;
      const cassetteId = row.cassette;
      return !selectedCassettes.some(
        (cassette) =>
          cassette.unitId == unitId && cassette.cassette == cassetteId
      );
    });
    selectedCassettes.length = 0;

    updateCorrelativeCassette();
  });

  $("#btnArmarCassette").click(function () {
    tableBuild.ajax.reload((response) => {
      // Unit details received from the server
      units = response;
      activateNewCassetteUnitSelect(response);
      activateOrganSelect();
      updateCorrelativeCassette();
    });

    let now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    $("#buildAt").val(now.toISOString().slice(0, 16));

    dlgArmarCassette.show();
  });

  $("#btnConfigurarCassette").click(() => {
    dlgConfigurarCassette.show();
  });

  tableIndex.on("select.dt deselect.dt", () => {
    setSelectedUnits();
  });

  tableBuild.on("select.dt deselect.dt", () => {
    setSelectedCassettes();
  });

  tableBuild.on("click", ".deleteOrgan", (e) => {
    const element = $(e.target);
    element.parent().remove();
  });

  $("#btnSaveCassette").click(() => {
    document.querySelector('#btnSaveCassette').disabled = true;
  });

  $("#btnSaveCassette").click(() => {
    let new_cassettes = [];
    tableBuild.rows().every(function (rowIdx, tableLoop, rowLoop) {
      const data = this.data();
      const cassette = tableBuild.cell({ row: rowIdx, column: 3 }).data();
      const cell = tableBuild.cell({ row: rowIdx, column: 4 });
      const cassetteOrgans = $(cell.node()).find(".unitSelectOrgan").children();

      const observationCell = tableBuild.cell({ row: rowIdx, column: 5 });
      const observation = $(observationCell.node()).find(".observation").val();

      let organs = [];

      for (const organGroup of cassetteOrgans) {
        const organId = $(organGroup).children(".organId").val();
        organs.push(organId);
      }

      if (organs.length > 0) {
        new_cassettes.push({
          id: data.unit_id,
          correlative: cassette,
          organs: organs,
          observation: observation,
        });
      }
    });
    const build_at = $("#buildAt").val();
    
    if (new_cassettes.length == 0) {
      Swal.fire({
        icon: "error",
        title: "No hay cassettes validos para armar",
      });
      document.querySelector('#btnSaveCassette').disabled = true;
    } else {
      console.log('4');

      Swal.fire({
        title: "Guardando...",
        allowOutsideClick: false,
      });
      Swal.showLoading();
      $.ajax(Urls["lab:cassette_build"](), {
        data: JSON.stringify({
          build_at: build_at,
          units: new_cassettes,
        }),

        method: "POST",

        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
        },

        contentType: "application/json; charset=utf-8",

        success: (data, textStatus) => {
          Swal.close();
          if (data.differences) {
            Swal.fire({
              icon: "info",
              title: "Se guardó con diferencias",
              text:
                "Hay órganos en la unidad que no están presentes en los cassettes creados, deseas ver las diferencias? o continuar en esta pagina?",
              showCancelButton: true,
              confirmButtonText: "Ir a ver las diferencias",
              cancelButtonText: "Continuar en esta pagina",
            }).then((result) => {
              if (result.isConfirmed) {
                window.location.replace(Urls["lab:cassette_difference"]());
              } else {
                location.reload();
              }
            });
          } else {
            Swal.close();
            Swal.fire({
              icon: "success",
              title: "Guardado exitosamente",
            }).then(() => {
              location.reload();
            });
          }
          document.querySelector('#btnSaveCassette').disabled = false;
          console.log('sucess');
        },
        error: (xhr, textStatus, error) => {
          console.log('failure');

          Swal.close();
          Swal.fire({
            icon: "error",
            title: "Ocurrió un error guardando los Cassettes",
          });
          console.error({ xhr, textStatus, error });
          document.querySelector('#btnSaveCassette').disabled = false;
        },
      });
    }
  });

  $("#btnGroupOrgans").click(() => {
    const selectedOrgans = rulesForm.groupOrgans.select2("data");
    let ids = [];
    let text = [];

    for (let select of selectedOrgans) {
      ids.push(parseInt(select.id));
      text.push(select.text);
    }
    rules.groups.push(ids);

    $("#tableGroupOrgans > tbody:last-child").append(
      `<tr>
            <td style="display: none;" class="groupIds">${ids.join(";")}</td>
            <td>${text.join(", ")}</td>
            <td>
                <button type="button" class="btn btn-danger">X</button>
            </td>
        </tr>`
    );

    rulesForm.groupOrgans.val(null).trigger("change");
  });

  $("#tableGroupOrgans").on("click", "button.btn-danger", function () {
    const ids = $(this).parent().siblings(".groupIds").text().split(";");
    const index = rules.groups.findIndex((group) => {
      return group === ids;
    });
    rules.groups.splice(index, 1);
    $(this).parents("tr").remove();
  });

  $("#selUniqueOrgans").on("select2:select select2:unselect", (e) => {
    const selected = $("#selUniqueOrgans")
      .select2("data")
      .map((row) => parseInt(row.id));

    rules.uniques = selected;
  });

  $("#dlgConfigurarCassette").on("select2:selecting", ".organSelect", (e) => {
    const id = parseInt(e.params.args.data.id);
    if (checkIfExists(id)) {
      Swal.fire({
        icon: "warning",
        title: "Ese organo ya fue seleccionado",
      });
      e.preventDefault();
    }
  });

  $("#inputMaxOrgans").on("input", (e) => {
    const value = parseInt(e.target.value);
    if (value < 0) {
      e.preventDefault();
      Swal.fire({
        icon: "warning",
        title: "Cantidad maxima no puede ser menor que 0.",
      });
      $(e.target).val(0);
    } else {
      rules.max = parseInt(e.target.value);
    }
  });

  $("#btnSaveConfiguration").click(() => {
    dlgConfigurarCassette.hide();
  });

  $(".detailTrigger").click(function (e) {
    e.preventDefault();
    const url = $(e.target).attr("href");
    $.get(url, function (data, textStatus) {
      Swal.fire({
        html: data,
        width: "80%",
      });
    });
  });

  $("#addOrgansButton").click(() => {
    const selectedOrgans = $("#selectNewOrgans").select2("data");
    const selectedRows = tableBuild.rows(".selected");
    for (const selectedOrgan of selectedOrgans) {
      selectedRows.every((rowIdx) => {
        const td = $(tableBuild.cell(rowIdx, 4).node());
        const cassetteOrgans = td.find(".unitSelectOrgan");
        const organ = organs.find((organ) => selectedOrgan.id == organ.pk);

        if (organ != undefined) {
          const organDOM = `<div class="btn-group mr-1" role="group">
                                    <button class="btn btn-secondary organId" type="button" value="${organ.pk}" disabled>${organ.fields.abbreviation}</button>
                                    <button class="btn btn-danger deleteOrgan" type="button">X</button>
                                </div>`;
          cassetteOrgans.append(organDOM);
        }
      });
    }
  });

  $("#btnCleanRules").click(() => {
    rules = {
      uniques: [],
      groups: [],
      max: 0,
    };

    rulesForm.uniqueOrgans.val(null).trigger("change");
    $("#tableGroupOrgans > tbody").empty();
    $("#inputMaxOrgans").val(0).trigger("change");
  });

  $("#clearOrgansButton").click(() => {
    tableBuild.rows().every((rowIdx) => {
      const td = $(tableBuild.cell(rowIdx, 4).node());
      const cassetteOrgans = td.find(".unitSelectOrgan");
      cassetteOrgans.empty();
    });
  });

  /* END EVENTS */
});
