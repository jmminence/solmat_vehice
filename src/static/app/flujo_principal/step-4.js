var researches;

function init_step_4(active = true) {
  var entryform_id = $("#entryform_id").val();
  var url = Urls.analysis_entryform_id(entryform_id);

  $.ajax({
    type: "GET",
    url: url,
    async: false,
  })
    .done(function (data) {
      $(".showShareBtn").removeClass("hidden");
      $(".showLogBtn").removeClass("hidden");
      $(".showSummaryBtn").removeClass("hidden");
      $(".showReceptionFileBtn").removeClass("hidden");

      $(".showAttachedFilesBtn").removeClass("hidden");
      loadAnalysisData(data);
      researches = data.research_types_list;

    })
    .fail(function () {
      console.log("Fail");
    });
}

function loadAnalysisData(data) {
  $("#analysis_group").empty();

  populateAnalysisData(data);

  if (data.analysis_with_zero_sample) {
    alertEmptyAnalysis();
  }
}

function alertEmptyAnalysis() {
  swal({
    title: "Información",
    text:
      "Hay servicios ingresados que no poseen muestras asociadas (en rojo), por lo cual recomendamos anular.",
    icon: "warning",
    showCancelButton: false,
  });
}

function loadResearches() {
  $("#service_researches").html(
    '<select multiple="multiple" size="10" id="researches_select"></select>'
  );

  $.each(researches, function (i, item) {
    $("#researches_select").append(
      $("<option>", {
        value: item.id,
        text: item.code + " " + item.name,
      })
    );
  });
  $("#researches_select").bootstrapDualListbox({
    nonSelectedListLabel: "No seleccionados",
    selectedListLabel: "Asociados al servicio",
    infoText: "Mostrando todos {0}",
    infoTextEmpty: "Lista vacía",
    filterTextClear: "Mostrar todos",
  });
}

function populateAnalysisData(data) {
  $("#analysis_group1").html("");
  $("#analysis_group2").html("");

  $.each(data.analyses, function (i, item) {
    var row = {};
    row.form_id = item.form_id;
    row.id = item.id;
    row.exam_name = item.exam_name;
    row.exam_stain = item.exam_stain;
    row.exam_pathologists_assignment = item.exam_pathologists_assignment;
    row.exam_chargeable = item.exam_chargeable;
    row.has_portal = item.has_portal;
    row.pre_report_started = item.pre_report_started;
    row.pre_report_ended = item.pre_report_ended;
    row.no_slice = item.slices.length;
    row.current_step = item.current_step;
    row.total_step = item.total_step;
    row.percentage_step = item.percentage_step;
    row.current_step_tag = item.current_step_tag;
    row.form_closed = item.form_closed;
    row.cancelled = item.cancelled;
    row.form_reopened = item.form_reopened;
    row.service = item.service;
    row.service_name = item.service_name;
    row.patologo_name = item.patologo_name;
    row.patologo_id = item.patologo_id;
    row.status = item.status;
    row.cancelled_by = item.cancelled_by;
    row.cancelled_at = item.cancelled_at;
    row.samples_count = item.samples_count;
    row.report_code = item.report_code;
    row.on_hold = item.on_hold;
    row.on_standby = item.on_standby;
    row.samples_charged = item.samples_charged;

    if (!row.cancelled) {
      addAnalysisElement(row);
    } else {
      addAnalysisElementCancelled(row);
    }

    $("#analysis-tab1").trigger("click");
  });
}

function addAnalysisElement(data) {
  var analysis_element5 = document.getElementById("analysis_element5");
  if (!analysis_element5) return;
  var analysisElementTemplate = analysis_element5.innerHTML;
  var templateFn = _.template(analysisElementTemplate);
  var templateHTML = templateFn(data);

  $("#analysis_group1").append(templateHTML);
}

function addAnalysisElementCancelled(data) {
  var analysis_element5 = document.getElementById("analysis_element5");
  if (!analysis_element5) return;
  var analysisElementTemplate = analysis_element5.innerHTML;
  var templateFn = _.template(analysisElementTemplate);
  var templateHTML = templateFn(data);

  $("#analysis_group2").append(templateHTML);
}

function deleteExternalReport(analysis_id, id) {
  var url = Urls.service_reports_id(analysis_id, id);
  $.ajax({
    type: "DELETE",
    url: url,
  })
    .done(function (data) {
      toastr.success("", "Informe eliminado exitosamente.");
      $("#sr-" + id).remove();
    })
    .fail(function () {
      toastr.error(
        "",
        "No ha sido posible eliminar el informe. Intente nuevamente."
      );
    });
}

function deleteServiceComment(analysis_id, id) {
  var url = Urls.service_comments_id(analysis_id, id);
  $.ajax({
    type: "DELETE",
    url: url,
  })
    .done(function (data) {
      toastr.success("", "Comentario eliminado exitosamente.");
      $("#sc-" + id).remove();
    })
    .fail(function () {
      toastr.error(
        "",
        "No ha sido posible eliminar el comentario. Intente nuevamente."
      );
    });
}

function deleteServiceResearch(analysis_id, id) {
  var url = Urls.service_researches_id(analysis_id, id);
  $.ajax({
    type: "DELETE",
    url: url,
  })
    .done(function (data) {
      toastr.success("", "Estudio eliminado exitosamente.");
      $("#rc-" + id).remove();
    })
    .fail(function () {
      toastr.error(
        "",
        "No ha sido posible eliminar el estudio. Intente nuevamente."
      );
    });
}

function showServiceReportsModal(
  id,
  service,
  case_closed,
  form_closed = false
) {
  $("#service_reports_internal").html("");
  if (service == 1) {
    var temp_internal = "<h4>Generado por el sistema</h4>";
    temp_internal += '<div class="col-sm-12 pl-2 pb-2">';
    temp_internal +=
      '<a target="_blank" href="/download-report/' +
      id +
      '"><i class="fa fa-download"></i> Descargar Informe</a>';
    temp_internal += "</div>";
    $("#service_reports_internal").html(temp_internal);
  }

  $("#service_reports_external").html("");
  $("#service_final_report").html("");
  var temp_external = "<h4>Agregados manualmente</h4>";
  temp_external += '<div id="reports_list" class="col-sm-12 pl-2 pb-2">';
  // var temp_final = "<h4>Agregados manualmente</h4>";
  // temp_final += '<div id="reports_list" class="col-sm-12 pl-2 pb-2">';
  var url = Urls.service_reports(id);
  $.ajax({
    type: "GET",
    url: url,
  })
    .done(function (data) {
      if (data.reports.length > 0) {
        if (!form_closed) {
          $.each(data.reports, function (index, value) {
            temp_external +=
              '<div id="sr-' +
              value.id +
              '"><button class="btn btn-sm btn-danger" onclick="deleteExternalReport(' +
              id +
              ", " +
              value.id +
              ')"><i class="fa fa-close"></i></button> <a target="_blank" href="' +
              value.path +
              '"><i class="fa fa-download"></i> ' +
              value.name +
              "</a></div>";
          });
        } else {
          $.each(data.reports, function (index, value) {
            if (value.final_report) {
              var temp_final = "<h4>Reporte Final</h4>";
              temp_final += '<div id="reports_list" class="col-sm-12 pl-2 pb-2">';
              temp_final +=
                '<div id="sr-' +
                value.id +
                '"><a target="_blank" href="' +
                value.path +
                '"><i class="fa fa-download"></i> ' +
                value.name +
                "</a></div>";
              $("#service_final_report").html(temp_final);
            } else {
              temp_external +=
                '<div id="sr-' +
                value.id +
                '"><a target="_blank" href="' +
                value.path +
                '"><i class="fa fa-download"></i> ' +
                value.name +
                "</a></div>";
            }
          });
        }
      } else {
        temp_external +=
          '<div><h5 class="not_available_text">No hay informes disponibles</h5>';
      }
      temp_external += "</div>";
      $("#service_reports_external").html(temp_external);
    })
    .fail(function () {
      console.log("Fail");
    });

  if (!form_closed) {
    var url = Urls.service_reports(id);
    var temp_uploader = "<h4>Cargador de informes</h4>";
    temp_uploader +=
      '<div class="col-sm-12"><form id="reports_uploader" action="' +
      url +
      '" class="dropzone needsclick">';
    temp_uploader += '<div class="dz-message" data-dz-message>';
    temp_uploader +=
      "<center><span><h3>Arrastra o selecciona el informe que deseas cargar</h3></span></center>";
    temp_uploader += "</div>";
    temp_uploader += "</form></div>";
    // temp += '<input type="reset" class="btn btn-secondary" data-dismiss="modal" value="Salir">';
    // temp += '<input type="button" class="btn btn-primary submit-file" value="Cargar Imágen""></div></div></div>';
    $("#service_reports_external_uploader").html("");
    $("#service_reports_external_uploader").html(temp_uploader);

    $("#reports_uploader").dropzone({
      autoProcessQueue: false,
      maxFilesize: 600,
      acceptedFiles: ".csv, .doc, .docx, .ods, .odt, .pdf, .xls, .xlsx, .xlsm",
      init: function () {
        var submitButton = document.querySelector(".submit-file");
        myDropzone = this;
        submitButton.addEventListener("click", function () {
          myDropzone.processQueue();
        });
        this.on("sending", function (file, xhr, formData) {
          lockScreen(1);
        });

        this.on("success", function (file, responseText) {
          if (responseText.ok) {
            toastr.success("", "Informe cargado exitosamente.");
            this.removeFile(file);
            $(".not_available_text").remove();
            $("#reports_list").prepend(
              '<div id="sr-' +
              responseText.file.id +
              '"><button class="btn btn-sm btn-danger" onclick="deleteExternalReport(' +
              id +
              ", " +
              responseText.file.id +
              ')"><i class="fa fa-close"></i></button> <a target="_blank" href="' +
              responseText.file.path +
              '"><i class="fa fa-download"></i> ' +
              responseText.file.name +
              "</a></div>"
            );
          } else {
            toastr.error(
              "",
              "No ha sido posible cargar el informe. Intente nuevamente."
            );
          }
          lockScreen(0);
        });

        this.on("error", function (file, response) {
          this.removeFile(file);
          bootbox.hideAll();
          toastr.error(
            "",
            "No ha sido posible cargar el informe. Intente nuevamente."
          );
          lockScreen(0);
        });

        this.on("addedfile", function () {
          if (this.files[1] != null) {
            this.removeFile(this.files[0]);
          }
        });
      },
    });
  }

  $("#service_reports_modal").modal("show");
}

function showServiceCommentsModal(id, case_closed, form_closed = false) {
  var temp = "";
  var url = Urls.service_comments(id);
  $.ajax({
    type: "GET",
    url: url,
  })
    .done(function (data) {
      if (data.comments.length > 0) {
        if (!form_closed) {
          $.each(data.comments, function (index, value) {
            temp +=
              '<p id="sc-' +
              value.id +
              '"><button class="btn btn-sm btn-danger" onclick="deleteServiceComment(' +
              id +
              ", " +
              value.id +
              ')"><i class="fa fa-close"></i></button> <b>' +
              value.done_by +
              " (" +
              value.created_at +
              "):</b> <br> " +
              value.text +
              "</p>";
          });
        } else {
          $.each(data.comments, function (index, value) {
            temp +=
              '<p id="sc-' +
              value.id +
              '"><b>' +
              value.done_by +
              " (" +
              value.created_at +
              "):</b> <br> " +
              value.text +
              "</p>";
          });
        }
      } else {
        temp +=
          '<p><h5 class="not_available_text">No hay comentarios disponibles</h5></p>';
      }

      if (!form_closed) {
        temp += "<h3>Ingresar nuevo comentario:</h3>";
        if (case_closed != 0) {
          temp +=
            '<div class="col-sm-12"><textarea data-id="' +
            id +
            '" class="form-control disabled" rows="3" id="input_service_comment"></textarea></div>';
        } else {
          temp +=
            '<div class="col-sm-12"><textarea data-id="' +
            id +
            '" class="form-control" rows="3" id="input_service_comment"></textarea></div>';
        }
      }

      $("#service_comments").html(temp);
    })
    .fail(function () {
      console.log("Fail");
    });

  $("#service_comments_modal").modal("show");
}

function showServiceResearchesModal(id, case_closed, form_closed = false) {
  $("#researches_modal_save_button").prop("disabled", false);
  var temp = "";
  var url = Urls.service_researches(id);
  $.ajax({
    type: "GET",
    url: url,
  })
    .done(function (data) {
      if (form_closed || case_closed) {
        $("#researches_modal_save_button").prop("disabled", true);
        $("#service_researches").html("");
        if (data.researches.length == 0) {
          $("#service_researches").append(
            "<p><h3 class='text-danger'>No hay estudios asociados al servicio.</h3></p>"
          );
        } else {
          $.each(data.researches, function (index, item) {
            $("#service_researches").append(
              "<p><h4>" +
              item.code +
              " " +
              item.name +
              ": " +
              item.description +
              "</h4></p>"
            );
          });
        }
      } else {
        loadResearches();
        $("#researches_select").data("id", id);
        $.each(data.researches, function (index, item) {
          if (
            $('#researches_select option[value="' + item.id + '"]').length == 0
          ) {
            $("#researches_select").append(
              $("<option>", {
                value: item.id,
                text: item.code + " " + item.name,
                disabled: "disabled",
                selected: "selected",
              })
            );
          } else {
            $('#researches_select option[value="' + item.id + '"]').prop(
              "selected",
              true
            );
          }
        });
        $("#researches_select").bootstrapDualListbox("refresh");
      }
    })
    .fail(function () {
      console.log("Fail");
    });
  $("#service_researches_modal").modal("show");
}

function saveServiceComment() {
  var id = $("#input_service_comment").data("id");
  var text = $("#input_service_comment").val();
  var url = Urls.service_comments(id);
  $.ajax({
    type: "POST",
    url: url,
    data: { comment: text },
  })
    .done(function (data) {
      $(".not_available_text").remove();
      $("#service_comments").prepend(
        '<p id="sc-' +
        data.comment.id +
        '"><button class="btn btn-sm btn-danger" onclick="deleteServiceComment(' +
        id +
        ", " +
        data.comment.id +
        ')"><i class="fa fa-close"></i></button> <b>' +
        data.comment.done_by +
        " (" +
        data.comment.created_at +
        "):</b> <br> " +
        data.comment.text +
        "</p>"
      );
    })
    .fail(function () {
      console.log("Fail");
    });
}

function saveServiceResearch() {
  var id = $("#researches_select").data("id");
  var url = Urls.service_researches(id);

  var values_selected = $("#researches_select").val();
  var values_disabled_selected = $(
    "#researches_select option[disabled]:selected"
  ).val();

  var values = values_selected.concat(values_disabled_selected);

  $.ajax({
    type: "POST",
    url: url,
    data: { researches: values },
  })
    .done(function (data) {
      // research_select.prop('disabled', true);
      if (data.ok) {
        toastr.success("Listo", "Estudios guardados exitosamente.");
      } else {
        toastr.error("Lo sentimos", "Error al guardar estudios.");
      }
    })
    .fail(function () {
      console.log("Fail");
    });
}

function closeService(form_id, analysis_id, can_close = true) {
  var got_reports = 0;
  var got_comments = 0;

  var url = Urls.service_comments(analysis_id);
  $.ajax({
    type: "GET",
    url: url,
    async: false,
  }).done(function (data) {
    if (data.comments.length > 0) {
      got_comments = data.comments.length;
    }
  });

  var url = Urls.service_reports(analysis_id);
  $.ajax({
    type: "GET",
    url: url,
    async: false,
  }).done(function (data) {
    if (data.reports.length > 0) {
      got_reports = data.reports.length;
    }
  });

  if (can_close) {
    bootbox.dialog({
      title: "<h3>Confirmación de cierre de servicio</h3>",
      message:
        "<p>El servicio posee " +
        got_reports +
        " reportes adjuntos y " +
        got_comments +
        " comentarios. \
        <p>¿Confirma que desea realizar el cierre del servicio?</p> \
        <p>Ingrese una fecha de cierre:</p> \
        <p><input type='text' required class='form-control input-closing-date-bootbox' /> </p>\
        <p>Ingrese el código del informe:</p> \
        <p><input type='text' required class='form-control input-report-code-bootbox' /></p> \
        <div class='alert alert-danger hidden alert-closing-service' role='alert'></div>",
      buttons: {
        cancel: {
          label: "Cancelar",
          className: "btn-danger",
        },
        ok: {
          label: "Confirmar",
          className: "btn-info",
          callback: function () {
            $(".alert-closing-service").html("");
            $(".alert-closing-service").addClass("hidden");
            var closing_date = $(".input-closing-date-bootbox").val();
            var report_code = $(".input-report-code-bootbox").val();
            var err = false;
            if (closing_date == "") {
              $(".alert-closing-service").append(
                "<p>Ingrese la fecha de cierre para continuar</p>"
              );
              $(".alert-closing-service").removeClass("hidden");
              err = true;
            }
            if (report_code == "") {
              $(".alert-closing-service").append(
                "<p>Ingrese el código del informe para continuar</p>"
              );
              $(".alert-closing-service").removeClass("hidden");
              err = true;
            }
            if (!err) {
              var url = Urls.close_service(form_id, closing_date);
              $.ajax({
                type: "POST",
                url: url,
                data: { "report-code": report_code },
              })
                .done(function (data) {
                  window.location.reload();
                })
                .fail(function () {
                  console.log("Fail");
                });
            } else {
              return false;
            }
          },
        },
      },
    });

    $(".input-closing-date-bootbox").datetimepicker({
      locale: "es",
      keepOpen: false,
      format: "DD-MM-YYYY",
      defaultDate: moment(),
    });
  } else {
    swal({
      title: "Información",
      text:
        "Lo sentimos, aún no es posible cerrar el servicio ya que no ha iniciado la lectura o finalizado el pre-informe.",
      icon: "error",
      showCancelButton: true,
    });
  }
}

function cancelService(form_id) {
  bootbox.dialog({
    title: "<h3>Confirmación de anulación de servicio</h3>",
    message:
      "<p>¿Confirma que desea realizar la anulación del servicio?</p> \
      <p>Ingrese una fecha de anulación:</p> \
      <input type='text' class='form-control input-cancel-date-bootbox' /> \
      <br><p>Comentario:</p> \
      <textarea row='3' required class='form-control input-cancel-comment-bootbox'></textarea>",
    buttons: {
      cancel: {
        label: "Cancelar",
        className: "btn-danger",
      },
      ok: {
        label: "Confirmar",
        className: "btn-info",
        callback: function () {
          var cancel_date = $(".input-cancel-date-bootbox").val();
          var comment = $(".input-cancel-comment-bootbox").val();

          if (!cancel_date || !comment) {
            toastr.error(
              "Complete la información solicitada.",
              "No ha sido posible continuar con la anulación"
            );
            return false;
          }
          var url = Urls.cancel_service(form_id);
          $.ajax({
            type: "POST",
            url: url,
            data: { date: cancel_date, comment: comment },
          })
            .done(function (data) {
              window.location.reload();
            })
            .fail(function () {
              console.log("Fail");
            });
        },
      },
    },
  });

  $(".input-cancel-date-bootbox").datetimepicker({
    locale: "es",
    keepOpen: false,
    format: "DD-MM-YYYY",
    defaultDate: moment(),
  });
}

function reopenSerivce(form_id) {
  bootbox.dialog({
    title: "<h3>Confirmación de reapertura del servicio</h3>",
    message:
      "<p>¿Confirma que desea realizar la reapertura del servicio?</p> \
      <p>Ingrese una fecha de reapertura:</p> \
      <input type='text' class='form-control input-cancel-date-bootbox' /> \
      <br><p>Comentario:</p> \
      <textarea row='3' required class='form-control input-cancel-comment-bootbox'></textarea>",
    buttons: {
      cancel: {
        label: "Cancelar",
        className: "btn-danger",
      },
      ok: {
        label: "Confirmar",
        className: "btn-info",
        callback: function () {
          var reopen_date = $(".input-cancel-date-bootbox").val();
          var comment = $(".input-cancel-comment-bootbox").val();

          if (!reopen_date || !comment) {
            toastr.error(
              "Complete la información solicitada.",
              "No ha sido posible continuar con la anulación"
            );
            return false;
          }
          var url = Urls.reopen_form(form_id);
          $.ajax({
            type: "POST",
            url: url,
            data: { date: reopen_date, comment: comment },
          })
            .done(function (data) {
              window.location.reload();
            })
            .fail(function () {
              console.log("Fail");
            });
        },
      },
    },
  });

  $(".input-cancel-date-bootbox").datetimepicker({
    locale: "es",
    keepOpen: false,
    format: "DD-MM-YYYY",
    defaultDate: moment(),
  });
}

function initPreReport(analysis_id) {
  bootbox.dialog({
    title: "<h3>Confirmación</h3>",
    message: "<p>¿Confirma que desea iniciar la lectura?</p>",
    buttons: {
      cancel: {
        label: "Cancelar",
        className: "btn-danger",
      },
      ok: {
        label: "Confirmar",
        className: "btn-info",
        callback: function () {
          var url = Urls.init_pre_report(analysis_id);
          $.ajax({
            type: "POST",
            url: url,
          })
            .done(function (data) {
              window.location.reload();
            })
            .fail(function () {
              console.log("Fail");
            });
        },
      },
    },
  });
}

function endPreReport(analysis_id) {
  $("#modalAnalysisId").val(analysis_id);
  $("#checkQAPreReport").modal("show");

  $(".input-end-pre-report-date-bootbox").datetimepicker({
    locale: "es",
    keepOpen: false,
    format: "DD-MM-YYYY HH:mm",
    defaultDate: moment(),
  });
}

$("#btnDoneQA").click(() => {
  let isAnyCheckboxFalse = false;
  $(".checkQA").each(function () {
    const isCurrentCheckboxChecked = $(this).is(":checked");
    if (!isCurrentCheckboxChecked) {
      isAnyCheckboxFalse = true;
    }
  });

  if (isAnyCheckboxFalse) {
    toastr.error(
      "Debe marcar todos los checks",
      "No ha sido posible continuar con el cierre."
    );
    return;
  }
  const analysis_id = $("#modalAnalysisId").val();
  const end_date = $(".input-end-pre-report-date-bootbox").val();
  const comment = JSON.stringify($("#preReportComment").val());

  $("#btnDoneQA").attr("disabled", true);

  var url = Urls.end_pre_report(analysis_id, end_date);
  $.ajax({
    type: "POST",
    url: url,
    data: {
      comment,
    },
  })
    .done(function (data) {
      window.location.reload();
    })
    .fail(function () {
      $("#btnDoneQA").attr("disabled", false);
    });
});

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

let blockButtonsToPortal = {}
function goToPortal(id, service, reportCode) {
  if (!(id in blockButtonsToPortal)) {
    blockButtonsToPortal[id] = false;
  }

  if (!blockButtonsToPortal[id]) {
    var url = Urls.consolidado(id);
    window.location.href = url;
  } else{
    blockButtonsToPortal[id] = true;

    setTimeout(() => {
      blockButtonsToPortal[id] = false; // Habilitar el botón después del tiempo de espera
    }, 8000);
  }
}

function startPause(id, hold) {
  const is_hold = hold;
  Swal.fire({
    title: "Ingrese motivo o comentario",
    input: "text",
    showCancelButton: true,
    confirmButtonText: "Ok",
    showLoaderOnConfirm: true,
    inputValidator: (value) => {
      if (!value) {
        return "Obligatorio.";
      }
    },
    allowOutsideClick: () => !Swal.isLoading(),
  }).then((result) => {
    if (result.isConfirmed) {
      Swal.showLoading();
      const motive = result.value;

      $.ajax(Urls["toggle_analysis_status"](id), {
        data: JSON.stringify({
          motive,
          is_hold,
        }),

        method: "POST",

        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
        },

        contentType: "application/json; charset=utf-8",

        success: (data, textStatus) => {
          Swal.close();
          window.location.reload();
        },
        error: (xhr, textStatus, error) => {
          Swal.close();
          Swal.fire({
            icon: "error",
            title: "Ocurrió un error.",
          });
          console.error({ xhr, textStatus, error });
        },
      });
    }
  });
}

function stopPause(id, hold) {
  const is_hold = hold;
  Swal.fire({
    title: "Se va a reanudar el servicio",
    showCancelButton: true,
    confirmButtonText: "Ok",
    showLoaderOnConfirm: true,
    allowOutsideClick: () => !Swal.isLoading(),
  }).then((result) => {
    if (result.isConfirmed) {
      Swal.showLoading();
      $.ajax(Urls["toggle_analysis_status"](id), {
        data: JSON.stringify({
          is_hold,
        }),

        method: "POST",

        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
        },

        contentType: "application/json; charset=utf-8",

        success: (data, textStatus) => {
          Swal.close();
          window.location.reload();
        },
        error: (xhr, textStatus, error) => {
          Swal.close();
          Swal.fire({
            icon: "error",
            title: "Ocurrió un error.",
          });
          console.error({ xhr, textStatus, error });
        },
      });
    }
  });
}

function onClickGrouper(id) {
  $("#groupersModal").modal("show");
  $("#newGroupAnalysis").val(id);
  const groupList = $("#groupList");
  groupList.empty();

  $.get(Urls["review:groupers"]() + `?pk=${id}`, (data, status) => {
    const groupers = JSON.parse(data.groupers);
    const selected = JSON.parse(data.selected);
    for (const group of groupers) {
      let classes = "btn ";
      let btnText;
      if (selected.some((element) => element.fields.grouper == group.pk)) {
        classes += "btn-danger";
        btnText = "Sacar del grupo";
      } else {
        classes += "btn-success";
        btnText = "Agregar al grupo";
      }
      const button = `<button class="${classes}" onclick="toggleAnalysisGrouper(${id}, ${group.pk})">${btnText}</button>`;
      const row = `<li class="list-group-item d-flex flex-row justify-content-between">${group.fields.name} (#${group.pk}) ${button}</li>`;
      groupList.append(row);
    }
  });
}

function toggleAnalysisGrouper(analysisPk, grouperPk) {
  $.ajax(Urls["review:groupers"](), {
    data: JSON.stringify({
      analysis_pk: analysisPk,
      grouper_pk: grouperPk,
    }),

    method: "PUT",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
    },
    contentType: "application/json; charset=utf-8",
    success: (data, textStatus) => {
      Swal.close();
      onClickGrouper(analysisPk);
    },
    error: (xhr, textStatus, error) => {
      Swal.close();
      Swal.fire({
        icon: "error",
        title: "Ocurrió un error.",
      });
      console.error({ xhr, textStatus, error });
    },
  });
}

function createGrouper() {
  const analysisPk = $("#newGroupAnalysis").val();
  const groupName = $("#newGroupName").val();
  $.ajax(Urls["review:groupers"](), {
    data: JSON.stringify({
      pk: analysisPk,
      name: groupName,
    }),

    method: "POST",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
    },
    contentType: "application/json; charset=utf-8",
    success: (data, textStatus) => {
      Swal.close();
      onClickGrouper(analysisPk);
    },
    error: (xhr, textStatus, error) => {
      Swal.close();
      Swal.fire({
        icon: "error",
        title: "Ocurrió un error.",
      });
      console.error({ xhr, textStatus, error });
    },
  });
}

function showServiceDeadlineModal(id) {
  $('#serviceDeadline_id').val(id);
  $('.assignment-deadline').datetimepicker({
    locale: 'es',
    keepOpen: false,
    format: 'DD-MM-YYYY'
  });

  var url = Urls.get_serviceDeadline(id);
  $.ajax({
    type: "GET",
    url: url,
  })
    .done(function (data) {
      if (data.exists) {
        var laboratoryDeadline = data["data"]["laboratoryDeadline"]
        var pathologistDeadline = data["data"]["pathologistDeadline"]
        var reviewDeadline = data["data"]["reviewDeadline"]
        var comment = data.comment
        $('#comment').val(comment);
        $('#serviceDeadline_exist').val(data.exists);
      } else {
        var laboratoryDeadline = date(data["data"]["laboratoryDeadline"], data.created_at).toLocaleDateString();
        var pathologistDeadline = date(data["data"]["pathologistDeadline"] + data["data"]["laboratoryDeadline"], data.created_at).toLocaleDateString();
        var reviewDeadline = date(data["data"]["reviewDeadline"] + data["data"]["pathologistDeadline"] + data["data"]["laboratoryDeadline"], data.created_at).toLocaleDateString();
        $('#serviceDeadline_exist').val(data.exists);
      }

      if (data["data"]["laboratoryDeadline"] == null) {
        document.getElementById('laboratoryDeadline').disabled = true;
        $('#laboratoryDeadline').val("No aplica");
      } else {
        document.getElementById('laboratoryDeadline').disabled = false;
        $('#laboratoryDeadline').val(laboratoryDeadline);
      }

      if (data["data"]["pathologistDeadline"] == null) {
        document.getElementById('pathologistDeadline').disabled = true;
        $('#pathologistDeadline').val("No aplica");
      } else {
        document.getElementById('pathologistDeadline').disabled = false;
        $('#pathologistDeadline').val(pathologistDeadline);
      }

      if (data["data"]["reviewDeadline"] == null) {
        document.getElementById('reviewDeadline').disabled = true;
        $('#reviewDeadline').val("No aplica");
      } else {
        document.getElementById('reviewDeadline').disabled = false;
        $('#reviewDeadline').val(reviewDeadline);
      }
    })
    .fail(function () {
      console.log("Fail")
    });
  $("#serviceDeadlineModal").modal("show");
}

function saveServiceDeadlineModal() {
  var id = $('#serviceDeadline_id').val();
  var data = $('#serviceDeadline_form input').serializeArray();
  var comment = $('#comment').val();

  data.push({ name: "comment", value: comment });
  var exist = $('#serviceDeadline_exist').val();

  if ((exist == "true" && comment != "") || exist == "false") {
    $.ajax({
      type: "POST",
      url: '/save_serviceDeadline/' + id,
      data: data,
      async: false,
    })
      .done(function () {
        toastr.success("Fechas guardadas exitosamente.", "Listo!");
        $("#serviceDeadlineModal").modal("hide");
      })
      .fail(function () {
        console.log("Fail");
      })
  } else {
    toastr.warning("Tiene que agregar un comentario");
  }

}

function date(days, start) {

  var startDate = new Date(start);
  var endDate = "", noOfDaysToAdd = days, count = -1;
  while (count < noOfDaysToAdd) {
    endDate = new Date(startDate.setDate(startDate.getDate() + 1));
    if (endDate.getDay() != 0 && endDate.getDay() != 6) {
      count++;
    }
  }
  return endDate;
}


// METHODS AND RESOURCES FOR THE OUTSOURCE FUNCTIONALITY
let customers = [];
let outsourceAddsCounter = 0;
let caseFiles = {} // Almacena solo los nuevos archivos adjuntados.
let analysis_id = -1;
async function outsource(analysisId) {
  $("#outsourceModal").modal("show");
  analysis_id = analysisId;
  caseFiles = {};
  outsourceAddsCounter = 0;

  await fetchCustomers();
  let outsources = await fetchOutsource();
  buildOutsourceAll(outsources)
}

function outsourceEdit(outsourceId) {
  let optionContent = document.getElementById(`option-content-${outsourceId}`);
  optionContent.parentNode.style.backgroundColor = '#B2DFDB';

  // custommer
  let optionCustomer = document.getElementById(`option-custommer-${outsourceId}`);
  optionCustomer.style.display = 'block';
  let optionCustomerList = document.getElementById(`customers_datalist-${outsourceId}`);
  content = ``;
  customers.forEach(custom => {
    content += `<option value="${custom.id}">${custom.name}</option>`
  });
  optionCustomerList.innerHTML = content;

  // comment
  let optionComment = document.getElementById(`option-comment-${outsourceId}`);
  let optionCommentContent = document.getElementById(`option-comment-content-${outsourceId}`);

  let optionCommentField = document.createElement('textarea');
  optionCommentField.id = `option-comment-field-${outsourceId}`;
  optionCommentField.setAttribute('row', '2');
  optionCommentField.classList.add('option-comment-field');
  optionCommentField.value = optionCommentContent.textContent;

  optionComment.appendChild(optionCommentField);
  optionCommentContent.remove();

  // files
  let optionFilesAttach = document.getElementById(`option-files-attach-${outsourceId}`);
  optionFilesAttach.style.display = 'block';
  let optionFiles = document.getElementById(`option-files-content-${outsourceId}`);
  let liFiles = optionFiles.getElementsByTagName('li');
  for (let i = 0; i < liFiles.length; i++) {
    let buttonFile = liFiles[i].getElementsByTagName('button')[0];
    buttonFile.style.display = 'block';
  }

  // Buttons

  let optionBtnEdit = document.getElementById(`option-edit-${outsourceId}`);
  optionBtnEdit.style.display = 'none';
  let optionBtnRemove = document.getElementById(`option-remove-${outsourceId}`);
  optionBtnRemove.style.display = 'none';


  let optionBtnSave = document.getElementById(`option-save-${outsourceId}`);
  optionBtnSave.style.display = 'block';
  let optionBtnCancel = document.getElementById(`option-cancel-${outsourceId}`);
  optionBtnCancel.style.display = 'block';
}
function outsourceAdd() {
  let outsourceId = `temp-${++outsourceAddsCounter}`;

  contentCustomers = ``;
  customers.forEach(custom => {
    contentCustomers += `<option value="${custom.id}">${custom.name}</option>`
  });

  let accordion = document.getElementById('accordion');
  let content = `
    <input type="checkbox" name="accordion" id="option-${outsourceId}" checked>
      <label for="option-${outsourceId}">Empresa: ${customers[0].name}<i class="fa fa-chevron-right"></i></label>
      <div class="option-content" id="option-content-${outsourceId}">
        <hr>
          <div class="option-custommer" id="option-custommer-${outsourceId}">
            <h4>Empresa:</h4>
            <select class="custom-select" id="customers_datalist-${outsourceId}">
            ${contentCustomers}
            </select>
          </div>
          <div class="option-comment" id="option-comment-${outsourceId}">
            <h4>Comentario:</h4>
            <textarea id="option-comment-field-${outsourceId}" row="2" class="option-comment-field"></textarea>
          </div>
          <div class="option-files">
            <div class="option-files-header">
              <h4>Archivos:</h4>
              <button type="button" class="btn btn-grey option-files-attach" id="option-files-attach-${outsourceId}" onclick="document.getElementById('option-attach-input-${outsourceId}').click();"
                style="display: block;"><i class="fa fa-paperclip"></i>
                Adjuntar</button>
              <input type="file" class="option-attach-input" id="option-attach-input-${outsourceId}" accept=".pdf" onchange="handleOptionAttachFile(event, '${outsourceId}')">
            </div>
            <ul class="option-files-content" id="option-files-content-${outsourceId}">
            </ul>
          </div>
          <div class="options-bar">
            <button type="button" class="btn btn-primary" id="option-save-${outsourceId}"
              onclick="handleSaveButton('${outsourceId}')">Guardar</button>
            <button type="button" class="btn btn-secondary" onclick="handleBtnCancelAdd('outsource-${outsourceId}')">Cancelar</button>
          </div>
      </div>`;
  let li = document.createElement('li');
  li.innerHTML = content;
  li.id = `outsource-${outsourceId}`
  li.style.backgroundColor = '#B2DFDB';
  accordion.appendChild(li);
}
function buildOutsourceInfo(outsource) {
  let outsourceId = outsource.id;

  contentCustomers = ``;
  customName = '';
  customers.forEach(custom => {
    contentCustomers += `<option value="${custom.id}">${custom.name}</option>`
    if (custom.id == outsource.customer_id) {
      customName = custom.name
    }
  });

  contentFiles = ``;
  outsource.files.forEach(file => {
    contentFiles += `<li id="${file.id}">
                    <button type="button" class="btn btn-danger option-file-btn" style="display: none;"
                      id="option-file-${file.id}" onclick="handleBtnRemoveFile('${file.id}')"><i class="fa fa-remove"></i></button>
                    <a target="_blank" href="${file.url}">${file.name}</a>
                  </li>`;
  });

  let content = `
    <li id="outsource-${outsourceId}">
    <input type="checkbox" name="accordion" id="option-${outsourceId}">
      <label for="option-${outsourceId}">Empresa: ${customName}<i class="fa fa-chevron-right"></i></label>
      <div class="option-content" id="option-content-${outsourceId}">
        <hr>
          <div class="option-custommer" id="option-custommer-${outsourceId}" style="display: none;">
            <h4>Empresa:</h4>
            <select class="custom-select" id="customers_datalist-${outsourceId}">
            ${contentCustomers}
            </select>
          </div>
          <div class="option-comment" id="option-comment-${outsourceId}">
            <h4>Comentario:</h4>
            <p id="option-comment-content-${outsourceId}">${outsource.comment}</p>
          </div>
          <div class="option-files">
            <div class="option-files-header">
              <h4>Archivos:</h4>
              <button type="button" class="btn btn-grey option-files-attach" id="option-files-attach-${outsourceId}" onclick="document.getElementById('option-attach-input-${outsourceId}').click();"
                style="display: none;"><i class="fa fa-paperclip"></i>
                Adjuntar</button>
              <input type="file" class="option-attach-input" id="option-attach-input-${outsourceId}" accept=".pdf" onchange="handleOptionAttachFile(event, '${outsourceId}')">
            </div>
            <ul class="option-files-content" id="option-files-content-${outsourceId}">
            ${contentFiles}
            </ul>
          </div>
          <div class="options-bar">
            <button type="button" class="btn btn-info" id="option-edit-${outsourceId}" onclick="outsourceEdit('${outsourceId}')"><i
              class="fa fa-edit"></i></button>
            <button type="button" class="btn btn-primary" id="option-save-${outsourceId}"
              onclick="handleSaveButton('${outsourceId}')" style="display: none;">Guardar</button>
            <button type="button" class="btn btn-danger" id="option-remove-${outsourceId}" onclick="handleBtnRemoveOutsource('outsource-${outsourceId}')"><i class="fa fa-remove"></i></button>
            <button type="button" class="btn btn-secondary" id="option-cancel-${outsourceId}" style="display: none;" onclick="handleBtnCancelEdit('outsource-${outsourceId}')">Cancelar</button>
          </div>
      </div>
      </li>`;

  return content;
}
function buildOutsourceAll(outsources) {
  let accordion = document.getElementById('accordion');

  contentAll = ``;
  for (let i = 0; i < outsources.length; i++) {
    contentAll += buildOutsourceInfo(outsources[i]);
  }
  accordion.innerHTML = contentAll;
}
function buildOutsourceOnlyOne(outsource, outsource_id) {
  let accordion = document.getElementById('accordion');
  let outsource_li = document.getElementById(`outsource-${outsource_id}`);

  outsource_li.outerHTML = buildOutsourceInfo(outsource);
}



function handleOptionAttachFile(event, outsourceId) {
  const file = event.target.files[0];
  let isRepeat = false;
  if (outsourceId in caseFiles) {
    for (let i = 0; i < caseFiles[outsourceId].length; i++) {
      if (caseFiles[outsourceId][i].name == file.name) {
        isRepeat = true;
        break;
      }
    }
    if (!isRepeat)
      caseFiles[outsourceId].push(file);
  } else {
    caseFiles[outsourceId] = [file]
  }
  if (!isRepeat) {
    let optionFilesContent = document.getElementById(`option-files-content-${outsourceId}`);
    let li = document.createElement('li');
    li.id = id = `temp-${file.name}`;
    let p = document.createElement('p');
    p.textContent = file.name;

    let buttonRemove = document.createElement('button');
    buttonRemove.classList.add('btn');
    buttonRemove.classList.add('btn-danger');
    buttonRemove.classList.add('option-file-btn');
    buttonRemove.onclick = function () {
      li.remove();
      let index = caseFiles[outsourceId].indexOf(file);
      caseFiles[outsourceId].splice(index, 1);
      event.target.value = '';
    }
    let i = document.createElement('i');
    i.classList.add('fa');
    i.classList.add('fa-remove');

    buttonRemove.appendChild(i);
    li.appendChild(buttonRemove);
    li.appendChild(p);

    optionFilesContent.appendChild(li);
  }
}
async function handleSaveButton(outsourceId) {
  // Obtener y validar los datos.
  try {
    let data = getAndValidateOutsourcePost(outsourceId);
    let outsource;
    if (outsourceId.includes('temp')) {
      outsource = await postOutsource(data);
    } else {
      outsource = await putOutsource(data);
    }


    buildOutsourceOnlyOne(outsource, outsourceId);

    toastr.success("Se guardó satisfactoriamente", "");
  } catch (error) {
    toastr.error(error, "Aviso");
  }
}
function handleBtnRemoveFile(fileId) {
  let file = document.getElementById(fileId);
  file.remove();
}
async function handleBtnCancelEdit(outsourceId) {
  outsourceId = outsourceId.replace('outsource-', '');
  let outsource = await fetchOutsourceById(outsourceId);
  buildOutsourceOnlyOne(outsource, outsourceId);
}
function handleBtnCancelAdd(outsourceId) {
  let oursource = document.getElementById(outsourceId);
  oursource.remove();
}
async function handleBtnRemoveOutsource(outsourceId) {
  Swal.fire({
    title: "Atención",
    text: "¿Estás seguro que deseas eliminar la tercerización?",
    icon: "warning",
    confirmButtonText: "Si",
    showCancelButton: true,
    cancelButtonText: "No",
  }).then(async (result) => {
    if (result.isConfirmed) {
      try {
        id = outsourceId.replace('outsource-', '');
        await deleteOutsourceById(id);

        handleBtnCancelAdd(outsourceId);
        toastr.success("Se eliminó satisfactoriamente", "");
      } catch (error) {
        toastr.error(error, "Aviso");
      }
    }
  });

}



// Services
async function fetchCustomers() {
  const response = await fetch('api/customers', {
    method: 'GET',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
    }
  });
  data = await response.json();
  customersTemporal = data.results;
  customers = [];

  customersTemporal.forEach((custom) => {
    if (custom.inter_lab) {
      customers.push(custom);
    }
  })

}
async function fetchOutsource() {
  const response = await fetch(`api/outsource/analysis/${analysis_id}`, {
    method: 'GET',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
    }
  });
  data = await response.json();

  return data;
}
async function fetchOutsourceById(outsourceId) {
  const response = await fetch(`api/outsource/${outsourceId}`, {
    method: 'GET',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
    }
  });
  data = await response.json();

  return data;
}
async function postOutsource(outsource) {
  csrftoken = $('input[name=csrfmiddlewaretoken]').val();

  const formData = new FormData();
  formData.append('analysis_id', outsource.analysis_id);
  formData.append('customer_id', outsource.customer_id);
  formData.append('comment', outsource.comment);
  for (let i = 0; i < outsource.attachedFiles.length; i++) {
    formData.append('attachedFiles', outsource.attachedFiles[i]);
  }

  const response = await fetch('api/outsource', {
    method: 'POST',
    headers: {
      // 'Content-Type': 'application/json;charset=utf-8',
      'X-CSRFToken': getCookie('csrftoken'),
    },
    body: formData
  });

  if (!response.ok) {
    await response.json().then(errorInfo => {
      throw new Error(errorInfo.error);
    });
  } else {
    data = await response.json();
    return data;
  }
}
async function putOutsource(outsource) {
  csrftoken = $('input[name=csrfmiddlewaretoken]').val();

  const formData = new FormData();
  formData.append('analysis_id', outsource.analysis_id);
  formData.append('customer_id', outsource.customer_id);
  formData.append('comment', outsource.comment);
  formData.append('files', outsource.files);

  for (let i = 0; i < outsource.attachedFiles.length; i++) {
    formData.append('attachedFiles', outsource.attachedFiles[i]);
  }


  const response = await fetch(`api/outsource/${outsource.id}`, {
    method: 'PUT',
    headers: {
      // 'Content-Type': 'application/json;charset=utf-8',
      'X-CSRFToken': getCookie('csrftoken'),
    },
    body: formData
  });

  if (!response.ok) {
    await response.json().then(errorInfo => {
      throw new Error(errorInfo.error);
    });
  } else {
    data = await response.json();
    return data;
  }
}
async function deleteOutsourceById(outsourceId) {
  const response = await fetch(`api/outsource/${outsourceId}`, {
    method: 'DELETE',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
    }
  });
  return data;
}


// Utils methods:
// Validation data
function getAndValidateOutsourcePost(outsourceId) {
  let customer_id = document.getElementById(`customers_datalist-${outsourceId}`).value;
  let comment = document.getElementById(`option-comment-field-${outsourceId}`).value;

  if (customer_id === undefined) {
    throw new Error('Faltó seleccionar una empresa.');
  }
  if (isEmpty(comment)) {
    throw new Error('Faltó especificar un comentario.');
  }

  let containerFiles = document.getElementById(`option-files-content-${outsourceId}`);
  let downloadFiles = containerFiles.getElementsByTagName('li');
  let files = [];
  for (let i = 0; i < downloadFiles.length; i++) {
    if (!downloadFiles[i].id.includes('temp')) {
      files.push(downloadFiles[i].id);
    }
  }
  if (files.length < 2 && (!(outsourceId in caseFiles) || caseFiles[outsourceId].length + files.length < 2)) {
    throw new Error('Es necesario agregar al menos dos archivos para una tercerización.');
  }

  return {
    'id': outsourceId,
    'analysis_id': analysis_id,
    'customer_id': customer_id,
    'comment': comment,
    'files': files,
    'attachedFiles': caseFiles[outsourceId] === undefined ? [] : caseFiles[outsourceId],
  };
}
function isEmpty(text) {
  return text.trim().replace(/\s/g, '').length === 0
}