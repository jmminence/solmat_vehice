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
  $("#releaseAt").val(now.toISOString().slice(0, 16));

  const tableList = $("#datatable").DataTable({
    dom: "Bfrtipl",

    processing: true,
    serverSide: true,

    ajax: {
      url: Urls["lab:slide_release"](),
    },

    columns: [
      { data: "id" },
      { data: "tag" },
      {
        data: "url",
        render: (data) => {
          if (data == null) {
            return `No`;
          } else {
            return `<a href="${data}">Si</a>`;
          }
        },
      },
      {
        data: "created_at",
        render: (data) => {
          const date = new Date(data);
          return date.toLocaleDateString();
        },
      },
    ],

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

    columnDefs: [{ targets: [0], width: "1rem" }],

    select: {
      style: "multi",
    },

    oLanguage: {
      sUrl: "https://cdn.datatables.net/plug-ins/1.10.16/i18n/Spanish.json",
    },
  }).on('search.dt', function (e, settings) {
    var search = settings.oPreviousSearch.sSearch
    if (search != "") {
      tableList.page.len(100);
    }
  });

  $("#btnRelease").click(() => {
    const releasedAt = $("#releaseAt").val();

    if (!releasedAt) {
      toastr.error("Fecha de disponibilizacion no puede estar vacia.");
      return;
    }

    let selectedSlidesPk = [];
    let tags = []
    let slidesCreated_at = []
    tableList
      .rows({ selected: true })
      .data()
      .each((test) => {
        selectedSlidesPk.push(test.id);
        tags.push(test.tag)
        slidesCreated_at.push(test.created_at)
      });
    console.log(SlidesDatesCompare(slidesCreated_at, releasedAt))
    if (SlidesDatesCompare(slidesCreated_at, releasedAt)) {
      $.ajax(Urls["lab:slide_release"](), {
        data: JSON.stringify({
          released_at: releasedAt,
          slides: selectedSlidesPk,
          tags: tags,
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
    } else {
      toastr.error("Fecha de disponibilizacion no puede ser menor a la creacion del slide.");
    }

  });

  $("#btnRefresh").click(() => {
    tableList.ajax.reload();
  });
});

function SlidesDatesCompare(SlidesDates, released_at) {
  let result = true;
  SlidesDates.forEach(date => {
    if (Date.parse(released_at) < Date.parse(date)) {
      result = false;
    }
  });
  return result;
}