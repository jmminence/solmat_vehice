$(document).ready(function () {
  /* VARIABLES */

  let now = new Date();
  let currentDate = now.toISOString().substring(0, 10);

  $("#doneAt").val(currentDate);

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

    oLanguage: {
      sUrl: "https://cdn.datatables.net/plug-ins/1.10.16/i18n/Spanish.json",
    },
  });

  /* END VARIABLES*/

  $("#btnArmarProceso").click(() => {
    let selected = [];
    tableIndex
      .rows({ selected: true })
      .data()
      .each((element) => {
        selected.push(element[0]);
      });

    let slash = window.location.href.lastIndexOf("/");
    let process = window.location.href.substr(slash + 1);

    const process_prototype = {
      keys: selected,
      done_at: $("#doneAt").val(),
    };

    $.post({
      url: Urls["lab:process_build"](process),
      data: JSON.stringify(process_prototype),
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
  });

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
});
