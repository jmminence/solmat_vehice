const dlgProcesarCassette = new bootstrap.Modal(
  document.getElementById("dlgProcess")
);

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

$(document).ready(function () {
  let now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  $("#processAt").val(now.toISOString().slice(0, 16));

  const tableList = $("#datatable").DataTable({
    dom: "Bfrtip",

    buttons: [
      {
        text: "Seleccionar todos",
        action: function () {
          tableList
            .rows({
              page: "current",
            })
            .select();
        },
      },

      {
        text: "Deseleccionar todos",
        action: function () {
          tableList
            .rows({
              page: "current",
            })
            .deselect();
        },
      },
    ],

    columnDefs: [{ targets: [0, 2], width: "1rem" }],

    select: {
      style: "multi",
    },

    paging: false,

    oLanguage: {
      sUrl: "https://cdn.datatables.net/plug-ins/1.10.16/i18n/Spanish.json",
    },
  });

  $(".detailTrigger").click(function (e) {
    e.preventDefault();
    const url = $(e.target).attr("href");
    $.get(url, function (data, textStatus) {
      console.log(data);
      Swal.fire({
        html: data,
        width: "80%",
      });
    });
  });

  $("#btnProcess").click(() => {
    const processAtInput = $("#processAt");
    const processedAt = new Date(processAtInput.val().substring(0, 10));
    const maxDate = new Date(processAtInput.attr("max"));
    const minDate = new Date(processAtInput.attr("min"));

    if (!processedAt) {
      toastr.error("Fecha de procesado no puede estar vacia.");
      return;
    }

    if (processedAt < minDate || processedAt > maxDate) {
      toastr.error(
        `Fecha de procesado no puede ser mayor que Hoy o menor que ${minDate.toLocaleDateString()}`
      );
      return;
    }

    let selectedCassettesPk = [];
    tableList
      .rows({ selected: true })
      .data()
      .each((test) => {
        selectedCassettesPk.push(test[0]);
      });

    $.ajax(Urls["lab:cassette_process"](), {
      data: JSON.stringify({
        processed_at: processAtInput.val(),
        cassettes: selectedCassettesPk,
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
});
