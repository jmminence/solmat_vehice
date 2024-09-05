$(document).ready(function () {
  /* VARIABLES */
  const dlgEdit = new bootstrap.Modal(document.getElementById("dlgEdit"));
  const dlgCreate = new bootstrap.Modal(document.getElementById("dlgCreate"));

  const newSelUnit = $("#newSelectUnit");
  const newBuildDate = $("#newBuildDate");
  const newSelOrgan = $("#newSelectOrgan");

  const editSelUnit = $("#editSelUnit");

  const select2Options = {
    width: "100%",
    ajax: {
      url: Urls["lab:unit_select_options"](),
      dataType: "json",
      delay: 250,
      data: (params) => {
        var query = {
          search: params.term,
          page: params.page || 1,
        };

        // Query parameters will be ?search=[term]&page=[page]
        return query;
      },
    },
  };

  newSelUnit.select2({
    ...select2Options,
    dropdownParent: $("#dlgCreate"),
  });

  editSelUnit.select2({
    ...select2Options,
    dropdownParent: $("#dlgEdit"),
  });

  const selOrgan = $("#selOrgan");
  const correlative = $("#correlative");
  const buildDate = $("#buildDate");

  let organs;
  let cassette;

  $.get(Urls["lab:organ_index"](), (data) => {
    organs = data;
    const options = organs.map((organ) => {
      return {
        id: organ.pk,
        text: organ.fields.name,
      };
    });
    selOrgan.select2({
      data: options,
      width: "100%",
      dropdownParent: $("#dlgEdit"),
    });
    newSelOrgan.select2({
      data: options,
      width: "100%",
      dropdownParent: $("#dlgCreate"),
    });
  });

  const tableIndex = $(".zero-configuration").DataTable({
    oLanguage: {
      sUrl: "https://cdn.datatables.net/plug-ins/1.10.16/i18n/Spanish.json",
    },

    rowsGroup: [0, 1, 2],
  });

  /* END VARIABLES */

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

  function getIdFromClassList(classList) {
    // Turn the event target's classList into an array
    const id = [...classList]
      // Find among the classes the one containing the id using regex
      .find((value) => /^id-/.test(value))
      // Split the class into 2 using `-` as separator and
      // get second part of the class containing the id
      .split("-")[1];
    return id;
  }

  function addToTable(selector, select) {
    const items = select.select2("data");
    select.val(null).trigger("change");
    const table = $(selector);
    for (const selected of items) {
      table.append(`<tr>
                          <td>${selected.id}</td>
                          <td>${selected.text}</td>
                          <td>
                              <button class="btn btn-danger id-${selected.id}">X</button>
                          </td>
                      </tr>`);
    }
  }

  /* END FUNCTIONS */

  /*  EVENTS  */

  $(".btnEdit").click((e) => {
    const id = getIdFromClassList(e.target.classList);

    $("#tableOrgans tbody").empty();

    $.get(Urls["lab:cassette_detail"](id), (data) => {
      cassette = JSON.parse(data.cassette)[0];
      cassette.organs = JSON.parse(data.organs);

      correlative.val(cassette.fields.correlative);
      buildDate.val(cassette.fields.build_at);

      const table = $("#tableOrgans > tbody:last-child");

      for (const organ of cassette.organs) {
        table.append(`<tr>
                          <td>${organ.pk}</td>
                          <td>${organ.fields.name}</td>
                          <td>
                              <button class="btn btn-danger id-${organ.pk}">X</button>
                          </td>
                      </tr>`);
      }
    });

    dlgEdit.show();
  });

  $(".btn-close").click(() => {
    dlgEdit.hide();
    dlgCreate.hide();
  });

  $("#btnAddOrgan").click(() => {
    addToTable("#tableOrgans > tbody:last-child", selOrgan);
  });

  $("#btnNewAddOrgan").click(() => {
    addToTable("#tableNewOrgans > tbody:last-child", newSelOrgan);
  });

  $("#tableOrgans, #tableNewOrgans").on("click", "button", (e) => {
    $(e.target).parents("tr").remove();
  });

  $("#btnSave").click(() => {
    const correlative_value = correlative.val();
    const buildDateValue = buildDate.val();
    const unitVal = editSelUnit.val();

    let organs = [];
    const rows = $("#tableOrgans > tbody").children();
    for (const row of rows) {
      organs.push(parseInt($(row).children("td:first-child").text()));
    }

    let editedCassette = {
      build_at: buildDateValue,
      correlative: correlative_value,
      organs: organs,
    };

    if (unitVal) {
      const unitId = parseInt(unitVal);
      if (Number.isInteger(unitId)) {
        editedCassette["unit_id"] = unitId;
      }
    }

    $.ajax(Urls["lab:cassette_detail"](cassette.pk), {
      data: JSON.stringify(editedCassette),

      method: "POST",

      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
      },

      contentType: "application/json; charset=utf-8",

      success: (data, textStatus) => {
        cassette = null;
        correlative.val("");
        buildDate.val("");
        editSelUnit.val("").trigger("change");
        Swal.fire({
          icon: "success",
          title: "Guardado",
        }).then(() => {
          location.reload();
        });
      },

      error: (xhr, textStatus, error) => {
        Swal.fire({
          icon: "error",
        });
      },
    });
  });

  $("#btnCreate").click(() => {
    dlgCreate.show();
  });

  $("#btnSaveNew").click(() => {
    const unit = newSelUnit.val();
    const build_at = newBuildDate.val();

    let organs = [];
    const rows = $("#tableNewOrgans > tbody").children();
    for (const row of rows) {
      organs.push(parseInt($(row).children("td:first-child").text()));
    }

    $.ajax(Urls["lab:cassette_build"](), {
      data: JSON.stringify({
        build_at: build_at,
        units: [
          {
            id: unit,
            organs: organs,
          },
        ],
        observation: "",
      }),

      method: "POST",

      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
      },

      contentType: "application/json; charset=utf-8",

      success: (data, textStatus) => {
        cassette = null;
        newBuildDate.val("");
        newSelUnit.val(null).trigger("change");

        Swal.fire({
          icon: "success",
          title: "Guardado",
        }).then(() => {
          location.reload();
        });
      },

      error: (xhr, textStatus, error) => {
        Swal.fire({
          icon: "error",
        });
      },
    });
  });

  /* END EVENTS  */
});
