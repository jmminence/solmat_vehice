Dropzone.autoDiscover = false;

let analysis = null;
let grouper = null;

$(document).ready(() => {
  $("#waiting, #formating, #reviewing, #sending, #finished")
    .sortable({
      connectWith: ".state",
    })
    .disableSelection();

  const dropZoneConfiguration = {
    dictDefaultMessage: "Arrastre sus archivos aqui",
    acceptedFiles: ".csv, .doc, .docx, .ods, .odt, .pdf, .xls, .xlsx, .xlsm",
    maxFilesize: 600,
    createImageThumbnails: false,
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
    },
    init: function () {
      this.on("processing", (file) => {
        if (parseInt(analysis) > 0) {
          this.options.url = Urls["review:files"](0, analysis);
        } else if (parseInt(grouper) > 0) {
          this.options.url = Urls["review:files"](1, grouper);
        } else {
          return;
        }
      });
      this.on("queuecomplete", () => {
        if (analysis) {
          refreshFileList(0, analysis);
        } else if (grouper) {
          refreshFileList(1, grouper);
        } else {
          return;
        }
      });
      this.on("complete", (file) => {
        this.removeFile(file);
      });
    },
  };

  let dropzone = new Dropzone("#newFiles", dropZoneConfiguration);
  let finalReportsDZ = new Dropzone("#fR", {
    ...dropZoneConfiguration,
    dictDefaultMessage: "Arrastre sus informes finales aqui",
    disablePreviews: true,
    init: function () {
      this.on("processing", (file) => {
        if (parseInt(analysis) > 0) {
          this.options.url = Urls["review:final_report"](0, analysis);
        } else if (parseInt(grouper) > 0) {
          this.options.url = Urls["review:final_report"](1, grouper);
        } else {
          return;
        }
      });
      this.on("queuecomplete", () => {
        if (analysis) {
          refreshFileList(0, analysis);
        } else if (grouper) {
          refreshFileList(1, grouper);
        } else {
          return;
        }
      });
      this.on("complete", (file) => {
        this.removeFile(file);
      });
    },
  });
  let attachedFilesDZ = new Dropzone("#attachedFiles", {
    ...dropZoneConfiguration,
    dictDefaultMessage: "Arrastre sus archivos adjuntos aqui",
    disablePreviews: true,
    init: function () {
      this.on("processing", (file) => {
        if (parseInt(analysis) > 0) {
          this.options.url = Urls["review:attachment"](0, analysis);
        } else if (parseInt(grouper) > 0) {
          this.options.url = Urls["review:attachment"](1, grouper);
        } else {
          return;
        }
      });
      this.on("queuecomplete", () => {
        if (analysis) {
          refreshFileList(0, analysis);
        } else if (grouper) {
          refreshFileList(1, grouper);
        } else {
          return;
        }
      });
      this.on("complete", (file) => {
        this.removeFile(file);
      });
    },
  });

  const selectRecipients = $(".selectRecipients");

  selectRecipients.select2();

  const selectMailList = $("#selectMailList");

  const dlgNewRecipient = new bootstrap.Modal(
    document.getElementById("recipientDialog"),
    {
      backdrop: "static",
    }
  );
  const dlgFileList = new bootstrap.Modal(
    document.getElementById("fileDialog"),
    {
      backdrop: "static",
    }
  );

  const dlgNewMailList = new bootstrap.Modal(
    document.getElementById("mailListDialog"),
    {
      backdrop: "static",
    }
  );

  const dlgSendMail = new bootstrap.Modal(
    document.getElementById("finalDialog"),
    {
      backdrop: "static",
    }
  );
  const newRecipientForm = $("#newRecipientForm");

  const newMailListForm = $("#newMailListForm");

  const dlgReportScore = new bootstrap.Modal(
    document.getElementById("reportScore_modal"),
    {
      backdrop: "static",
    }
  );
  const dlgDiagnosticScore = new bootstrap.Modal(
    document.getElementById("diagnosticScore_modal"),
    {
      backdrop: "static",
    }
  );

  let waiting;
  let formating;
  let reviewing;
  let sending;
  let finished;

  Promise.all([
    getReviews(0),
    getReviews(1),
    getReviews(2),
    getReviews(3),
    getReviews(4),
  ]).then((values) => {
    waiting = parseResponse(values[0]);
    formating = parseResponse(values[1]);
    reviewing = parseResponse(values[2]);
    sending = parseResponse(values[3]);
    finished = parseResponse(values[4]);

    populateList("#waiting", waiting);
    populateList("#formating", formating);
    populateList("#reviewing", reviewing);
    populateList("#sending", sending);
    populateList("#finished", finished);
  });

  /* FUNCTIONS */
  async function getReviews(stage) {
    let response = await fetch(Urls["review:list"](stage));

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  }

  function parseResponse(response) {
    return {
      analysis: response.analysis.map((row) => {
        const data = JSON.parse(row);
        return {
          analysis: data[0],
          case: data[1],
          exam: data[2],
          customer: data[3],
        };
      }),
      groupers: response.grouper,
    };
  }

  function populateList(id, array, filter = null) {
    const list = $(id);
    list.empty();

    let items = array.groupers;
    if (filter != null) {
      items = array.groupers.filter((item) => {
        if (item.case.no_caso.toLowerCase().includes(filter)) {
          return true;
        }

        if (item.customer.name.toLowerCase().includes(filter)) {
          return true;
        }

        return false;
      });
    }
    for (const item of items) {
      list.append(`<li class="list-group-item list-group-item-info">
                        <small>
                            <a href="#" class="serviceItem" id="${item.group.id}" data-state="${id}" data-analysis="" data-grouper="${item.group.id}">
                                ${item.case.no_caso} - ${item.group.title} - ${item.customer.name}
                            </a>
                        </small>
                    </li>`);
    }

    items = array.analysis;
    if (filter != null) {
      items = array.analysis.filter((item) => {
        if (item.case.fields.no_caso.toLowerCase().includes(filter)) {
          return true;
        }

        if (item.exam.fields.name.toLowerCase().includes(filter)) {
          return true;
        }

        if (item.customer.fields.name.toLowerCase().includes(filter)) {
          return true;
        }

        return false;
      });
    }
    for (const item of items) {
      list.append(`<li class="list-group-item">
                        <small>
                            <a href="#" class="serviceItem" id="${item.analysis.pk}" data-state="${id}" data-analysis="${item.analysis.pk}" data-grouper="">
                                ${item.case.fields.no_caso} - ${item.exam.fields.name} - ${item.customer.fields.name}
                            </a>
                        </small>
                    </li>`);
    }

    updateCount(id);
  }

  function updateCount(id) {
    if (!id.includes("#")) {
      id = `#${id}`;
    }
    const count = $(`${id} li`).length;
    $(`${id}Count`).text(`(${count})`);
  }

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

  function updateSelectRecipients() {
    let url = "";
    if (analysis) {
      url = Urls["review:recipients"](0, analysis);
    } else if (grouper) {
      url = Urls["review:recipients"](1, grouper);
    } else {
      return;
    }

    $.get(url, (response) => {
      const selectedRecipients = JSON.parse(response["current_recipients"]);
      const mailLists = JSON.parse(response["mail_lists"]);

      $("#mainRecipient").val(null).trigger("change");
      $("#ccRecipient").val(null).trigger("change");

      if (selectMailList.hasClass("select2-hidden-accessible")) {
        selectMailList.select2("destroy");
      }

      selectMailList.empty();

      selectMailList.append(
        `<option value="-1" selected>Agregar una lista de correos</option>`
      );
      for (const option of mailLists) {
        selectMailList.append(
          `<option value="${option.pk}">${option.fields.name}</option>`
        );
      }

      selectMailList.select2();

      const selectedMainRecipients = selectedRecipients
        .filter((selected) => selected.fields.is_main)
        .flatMap((selected) => [selected.fields.recipient]);

      const selectedCCRecipients = selectedRecipients
        .filter(
          (selected) =>
            !selected.fields.is_main &&
            !selectedMainRecipients.includes(selected.fields.recipient)
        )
        .flatMap((selected) => [selected.fields.recipient]);

      $("#mainRecipient").val(selectedMainRecipients).trigger("change");
      $("#ccRecipient").val(selectedCCRecipients).trigger("change");
    });
  }

  /* EVENTS */

  $(".state").on("sortreceive", (event, ui) => {
    const currentState = ui.sender[0].id;
    const nextState = event.target.id;
    const dataState = document.getElementById(ui.item[0].children[0].children[0].id);
    dataState.setAttribute('data-state','#'+nextState);
    let state;


    switch (nextState) {
      case "waiting":
        state = 0;
        break;
      case "formating":
        state = 1;
        break;
      case "reviewing":
        state = 2;
        break;
      case "sending":
        state = 3;
        break;
      case "finished":
        state = 4;
        break;
    }
    updateCount(currentState);
    updateCount(nextState);

    let url = getUrlByType(ui, "review:stage");

    $.ajax(url, {
      data: JSON.stringify({
        state: state,
      }),

      method: "POST",

      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
      },

      contentType: "application/json; charset=utf-8",

      success: (data, textStatus) => {
        toastr.success("Actualizado exitosamente.");
      },

      error: (xhr, textStatus, error) => {
        toastr.error("Ocurrió un error.");
        location.reload();
      },
    });
  });

  $("ul.list-group").on("click", ".serviceItem", (e) => {
    e.preventDefault();
    if (e.target.dataset.analysis) {
      analysis = e.target.dataset.analysis;
      grouper = null;
      state = e.target.dataset.state;
      refreshFileList(0, analysis,state);
    }

    if (e.target.dataset.grouper) {
      analysis = null;
      grouper = e.target.dataset.grouper;
      state = e.target.dataset.state;
      refreshFileList(1, grouper,state);
    }

    const title = `Archivos: ${e.target.innerText}`;
    $("#fileDialog h5.modal-title").text(title);
    dlgFileList.show();

    updateSelectRecipients();
  });
  
  $("#reviewing").on("sortreceive", (e, ui) => {
    dlgReportScore.show();
    const dataset = ui.item[0].children[0].children[0].dataset;

    analysis = parseInt(dataset.analysis);
    grouper = parseInt(dataset.grouper);
    var type = "";
    if(analysis){
      type = "analysis";
      var service_id = analysis;
    }else{
      type = "group";
      var service_id = grouper;
    }
     $('#score_service_id').val(service_id);
     $('#reportScore_type').val(type);
     $('#score_report').val("");
     var url = Urls.get_scores(type, service_id);
     $.ajax({
         type: "GET",
         url: url,
     })
      .done(function (data) {
          if (data.score_report) {
              $('#score_report').val(data.score_report.toString().replace(",", "."));
          }
      })
      .fail(function () {
          console.log("Fail")
      });
  });

  $(document).on('click', '.saveScores', function(e){
    var id = $('#score_service_id').val();
    var data = $('#reportScore_form').serialize();
    var type = $('#reportScore_type').val();
    var float = $('#score_report').serializeArray();
    if (typeof parseFloat(float[0].value) === 'number' &&
    !Number.isNaN(parseFloat(float[0].value))){
      console.log("test")
      $.ajax({
          type: "POST",
          url: '/save-scores/'+type+'/'+id,
          data: data,
          async: false,
      })
      .done(function () {
          toastr.success("Notas guardadas exitosamente.", "Listo!");
          dlgReportScore.hide();
      })
      .fail(function () {
          console.log("Fail");
      })
    }else{
      toastr.warning("El campo debe ser numerico");
    }
});

$("#sending").on("sortreceive", (e, ui) => {
  dlgDiagnosticScore.show();
  const dataset = ui.item[0].children[0].children[0].dataset;

  analysis = parseInt(dataset.analysis);
  grouper = parseInt(dataset.grouper);
  var type = "";
    if(analysis){
      type = "analysis";
      var service_id = analysis;
    }else{
      type = "group";
      var service_id = grouper;
    }
   $('#score_service_id').val(service_id);
   $('#diagnosticScore_type').val(type);
   $('#score_diagnostic').val("");
   var url = Urls.get_scores(type, service_id);
   $.ajax({
       type: "GET",
       url: url,
   })
    .done(function (data) {
        if (data.score_diagnostic) {
            $('#score_diagnostic').val(data.score_diagnostic.toString().replace(",", "."));
        }
    })
    .fail(function () {
        console.log("Fail")
    });
});

$(document).on('click', '.saveScores', function(e){
  var id = $('#score_service_id').val();
  var data = $('#diagnosticScore_form').serialize();
  var type = $('#reportScore_type').val();
  var float = $('#score_report').serializeArray();
  if (typeof parseFloat(float[0].value) === 'number' &&
  !Number.isNaN(parseFloat(float[0].value))){
    $.ajax({
        type: "POST",
        url: '/save-scores/'+type+'/'+id,
        data: data,
        async: false,
    })
    .done(function () {
        toastr.success("Notas guardadas exitosamente.", "Listo!");
        dlgDiagnosticScore.hide();
    })
    .fail(function () {
        console.log("Fail");
    })
  }else{
    toastr.warning("El campo debe ser numerico");
  }
});

  $("#finished").on("sortreceive", (e, ui) => {
    const recipientUrl = getUrlByType(ui, "review:analysis_emails");
    const dataset = ui.item[0].children[0].children[0].dataset;

    analysis = parseInt(dataset.analysis);
    grouper = parseInt(dataset.grouper);

    dlgSendMail.show();
    $.get(recipientUrl, (response) => {
      let data = JSON.parse(response);
      $("#finalRecipientsList").empty();
      for (const recipient of data) {
        $("#finalRecipientsList").append(
          `<p>${recipient.fields.first_name} &lt;${recipient.fields.email}&gt;<p>`
        );
      }
    });
    const fileUrl = getUrlByType(ui, "review:files");
    $.ajax(fileUrl, {
      method: "GET",

      success: (data, textStatus) => {
        const finalReports = data.final_reports;
        const finalReportsList = $("#finalDlgReportList");
        finalReportsList.empty();

        let index = 1;
        for (const file of finalReports) {
          finalReportsList.append(
            `<li class="list-group-item">
<a href="${file.download}" target="_BLANK">${file.name} (${file.original})</a>
<div class="input-group">
  <div class="input-group-prepend">
    <span class="input-group-text" id="basic-addon1">Correlativo:</span>
  </div>
  <input type="text" class="form-control finalFiles" data-id="${file.id}" value="${index}" aria-label="Correlativo" aria-describedby="basic-addon1">
  <div class="input-group-append">
    <button type="button" class="btn btn-outline-danger float-right" onclick="deleteFileUrl('${file.delete_url}')">&times;</button>
  </div>
</div>
</li>`
          );
        }
        index += 1;

        const attachments = data.attachments;
        const attachmentsList = $("#finalDlgAttachmentList");
        attachmentsList.empty();

        for (const file of attachments) {
          attachmentsList.append(
            `<li class="list-group-item">
<a href="${file.download}" target="_BLANK">${file.name}</a>
<button type="button" class="btn btn-outline-danger float-right" onclick="deleteFileUrl('${file.delete_url}')">&times;</button>
</li>`
          );
        }
      },
      error: (xhr, textStatus, error) => {
        toastr.error(error);
      },
    });
  });

  $("#search").on("input", (e) => {
    const queryString = e.target.value.toLowerCase();

    populateList("#waiting", waiting, queryString);
    populateList("#formating", formating, queryString);
    populateList("#reviewing", reviewing, queryString);
    populateList("#sending", sending, queryString);
    populateList("#finished", finished, queryString);
  });

  selectMailList.change((e) => {
    const mailListPk = selectMailList.select2("data")[0].id;

    if (mailListPk == -1) return;

    $.ajax(Urls["review:mail_list"](mailListPk), {
      method: "GET",
      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
      },
      contentType: "application/json; charset=utf-8",

      success: (response) => {
        const recipients = response;

        const mains = recipients
          .filter((recipient) => recipient.is_main)
          .map((recipient) => recipient.id);
        const ccs = recipients
          .filter((recipient) => !recipient.is_main)
          .map((recipient) => recipient.id);

        $("#mainRecipient").val(mains).trigger("change");
        $("#ccRecipient").val(ccs).trigger("change");
      },
    });
  });

  $("#btnCreateRecipient").click(() => {
    dlgFileList.hide();
    dlgNewRecipient.show();
  });

  $("#btnCreateMailList").click(() => {
    dlgFileList.hide();
    dlgNewMailList.show();
  });

  newRecipientForm.submit((e) => {
    e.preventDefault();
    const newRecipient = newRecipientForm
      .serializeArray()
      .reduce((acc, input) => ({ ...acc, [input.name]: input.value }), {});

    Swal.fire({
      title: `Se creará un nuevo destinatario en el sistema.`,
      text: "Se recargará la pagina después de guardar.",
      icon: "info",
      showCancelButton: true,
      cancelButtonText: "Cancelar",
      confirmButtonText: "Aceptar",
    }).then((result) => {
      if (result.isConfirmed) {
        $.ajax(Urls["review:create_recipient"](), {
          method: "POST",
          data: JSON.stringify(newRecipient),
          headers: {
            "X-CSRFToken": getCookie("csrftoken"),
          },
          contentType: "application/json; charset=utf-8",

          success: () => {
            toastr.success("Destinatario creado.");
            newRecipientForm.trigger("reset");
            updateSelectRecipients();
            dlgFileList.show();
            dlgNewRecipient.hide();
            location.reload();
          },
          error: (err) => {
            toastr.error("Ha ocurrido un error.");
          },
        });
      }
    });
  });

  newMailListForm.submit((e) => {
    e.preventDefault();
    let newMailList = newMailListForm
      .serializeArray()
      .reduce((acc, input) => ({ ...acc, [input.name]: input.value }), {});

    const mains = $("#mainRecipient")
      .select2("data")
      .map((main) => {
        return {
          id: main.id,
          is_main: true,
        };
      });
    const ccs = $("#ccRecipient")
      .select2("data")
      .map((cc) => {
        return {
          id: cc.id,
          is_main: false,
        };
      });

    newMailList.recipients = [...mains, ...ccs];

    Swal.fire({
      title: `Se guardaran los destinatarios para este análisis.`,
      icon: "info",
      showCancelButton: true,
      cancelButtonText: "Cancelar",
      confirmButtonText: "Aceptar",
    }).then((result) => {
      if (result.isConfirmed) {
        $.ajax(Urls["review:mail_list"](analysis), {
          method: "POST",
          data: JSON.stringify(newMailList),
          headers: {
            "X-CSRFToken": getCookie("csrftoken"),
          },
          contentType: "application/json; charset=utf-8",

          success: (response) => {
            toastr.success("Lista de correos creada.");
            newMailListForm.trigger("reset");
            dlgFileList.show();
            dlgNewMailList.hide();
          },
          error: (err) => {
            toastr.error("Ha ocurrido un error.");
          },
        });
      }
    });
  });

  $("#btnSaveRecipients").click(() => {
    const mainRecipients = $("#mainRecipient").select2("data");
    const ccRecipients = $("#ccRecipient").select2("data");

    let recipients = [];

    for (const [index, element] of mainRecipients.entries()) {
      recipients.push({
        pk: element.id,
        is_main: true,
      });
    }

    for (const [index, element] of ccRecipients.entries()) {
      recipients.push({
        pk: element.id,
        is_main: false,
      });
    }
    Swal.fire({
      title: `Se guardaran los destinatarios para este análisis.`,
      icon: "info",
      showCancelButton: true,
      cancelButtonText: "Cancelar",
      confirmButtonText: "Aceptar",
    }).then((result) => {
      if (result.isConfirmed) {
        let url = "";
        if (analysis) {
          url = Urls["review:recipients"](0, analysis);
        } else if (grouper) {
          url = Urls["review:recipients"](1, grouper);
        } else {
          return;
        }
        $.ajax(url, {
          method: "POST",
          data: JSON.stringify(recipients),
          headers: {
            "X-CSRFToken": getCookie("csrftoken"),
          },
          contentType: "application/json; charset=utf-8",

          success: () => {
            toastr.success("Actualizado exitosamente.");
          },

          error: () => {
            toastr.error("Ha ocurrido un error.");
          },
        });
      }
    });
  });

  $("#btnUpdateMailList").click(() => {
    const mailListPk = selectMailList.select2("data")[0].id;
    const mailListName = selectMailList.select2("data")[0].text;

    if (mailListPk == -1) return;

    const mains = $("#mainRecipient")
      .select2("data")
      .map((main) => {
        return {
          id: main.id,
          is_main: true,
        };
      });
    const ccs = $("#ccRecipient")
      .select2("data")
      .map((cc) => {
        return {
          id: cc.id,
          is_main: false,
        };
      });

    const recipients = [...mains, ...ccs];

    Swal.fire({
      title: `Se actualizara la lista de correos ${mailListName}.`,
      icon: "info",
      showCancelButton: true,
      cancelButtonText: "Cancelar",
      confirmButtonText: "Aceptar",
    }).then((result) => {
      if (result.isConfirmed) {
        $.ajax(Urls["review:mail_list"](mailListPk), {
          method: "PUT",
          data: JSON.stringify(recipients),
          headers: {
            "X-CSRFToken": getCookie("csrftoken"),
          },
          contentType: "application/json; charset=utf-8",

          success: (response) => {
            toastr.success(`Lista de correos ${mailListName} actualizada.`);
          },
          error: (err) => {
            toastr.error("Ha ocurrido un error.");
          },
        });
      }
    });
  });

  $("#fileDialog").on("hidden.bs.modal", () => {
    dropzone.removeAllFiles();
  });

  $("#sendEmailBtn").click(() => {
    const language = $("#language").val();
    const template = $("#template").val();
    let fileInputs = $("#finalDlgReportList .finalFiles");

    let correlatives = {};
    for (const input of fileInputs) {
      correlatives[input.dataset.id] = input.value;
    }

    Swal.fire({
      title:
        "Se enviara un correo a los destinatarios indicados, ¿esta seguro?",
      showCancelButton: true,
      cancelButtonText: "Cancelar",
    }).then((result) => {
      if (result.isConfirmed) {
        let data = {
          pk: null,
          analysis: false,
          grouper: false,
          test: false,
          language: language,
          template: template,
          correlatives: correlatives,
        };
        if (analysis) {
          data.analysis = true;
          data.pk = analysis;
        } else if (grouper) {
          data.grouper = true;
          data.pk = grouper;
        }
        if (language != -1 && template != -1) {
          toastr.info("Enviando correos...");
          $.ajax(Urls["review:send_email"](), {
            method: "PUT",
            data: JSON.stringify(data),
            headers: {
              "X-CSRFToken": getCookie("csrftoken"),
            },
            contentType: "application/json; charset=utf-8",

            success: (response) => {
              if (response.status === "OK") {
                toastr.success("Correo enviado.");
                setTimeout(location.reload, 1500);
              } else {
                toastr.error("Ocurrió un error.");
                switch (response.code) {
                  case 0:
                    toastr.warning(
                      "No se encontró informe disponible para enviar."
                    );
                    break;
                  case 1:
                    toastr.warning(
                      "No seleccionó lista de correo, o la lista esta vacia."
                    );
                    break;
                  case 2:
                    toastr.warning("Ocurrio un error enviando el correo.");
                    break;
                }
              }
            },
          });
        } else {
          toastr.warning("Debe seleccionar los campos");
        }
      } else {
        toastr.info("Operacion cancelada.");
        setTimeout(location.reload, 1500);
      }
    });
  });
  $("#sendTestEmailBtn").click(() => {
    const language = $("#language").val();
    const template = $("#template").val();
    let fileInputs = $("#finalDlgReportList .finalFiles");
    let correlatives = {};
    for (const input of fileInputs) {
      correlatives[input.dataset.id] = input.value;
    }

    Swal.fire({
      title: "Se enviara un correo de prueba al usuario, ¿esta seguro?",
      showCancelButton: true,
      cancelButtonText: "Cancelar",
    }).then((result) => {
      if (result.isConfirmed) {
        let data = {
          pk: null,
          analysis: false,
          grouper: false,
          test: true,
          template: template,
          language: language,
          correlatives: correlatives,
        };

        if (analysis) {
          data.analysis = true;
          data.pk = analysis;
        } else if (grouper) {
          data.grouper = true;
          data.pk = grouper;
        }

        if (language != -1 && template != -1) {
          toastr.info("Enviando correos...");
          $.ajax(Urls["review:send_email"](), {
            method: "PUT",
            data: JSON.stringify(data),
            headers: {
              "X-CSRFToken": getCookie("csrftoken"),
            },
            contentType: "application/json; charset=utf-8",

            success: (response) => {
              console.log(response)
              if (response.status === "OK") {
                toastr.success("Correo enviado.");
              } else {
                toastr.error("Ocurrió un error.");
                switch (response.code) {
                  case 0:
                    toastr.warning(
                      "No se encontró informe disponible para enviar."
                    );
                    break;
                  case 1:
                    toastr.warning(
                      "No seleccionó lista de correo, o la lista esta vacia."
                    );
                    break;
                  case 2:
                    toastr.warning("Ocurrio un error enviando el correo.");
                    break;
                }
              }
            },
          });
        } else {
          toastr.warning("Debe seleccionar los campos");
        }
      } else {
        toastr.info("Operacion cancelada.");
        setTimeout(location.reload, 1500);
      }
    });
  });
});

function getStateName(state) {
  switch (parseInt(state)) {
    case 0:
      return "En Espera";
    case 1:
      return "Formato";
    case 2:
      return "Revision";
    case 3:
      return "Por enviar";
  }
}

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

function refreshFileList(type, pk, state=null) {
  $.ajax(Urls["review:files"](type, pk), {
    method: "GET",

    success: (data, textStatus) => {
      const prereports = data.prereports;
      const prereportList = $("#prereportList");
      prereportList.empty();
      
      if(state == "#sending"){
        for (const file of prereports) {
          prereportList.append(
            `<li class="list-group-item"><a>${file.name}</a></li>`
          );
        }
      }else{
        for (const file of prereports) {
          prereportList.append(
            `<li class="list-group-item"><a href="${file.download}" target="_BLANK">${file.name}</a></li>`
          );
        }
      }
      

      const reviews = data.reviews;
      const reviewList = $("#reviewList");
      reviewList.empty();

      for (const file of reviews) {
        const created = new Date(file.created_at);
        reviewList.append(
          `<li class="list-group-item">
              <a href="${file.download}" target="_BLANK">
                ${file.name}
                - ${getStateName(file.state)}
                - ${created.toLocaleString()}
              </a>
<button type="button" class="btn btn-outline-danger float-right" onclick="deleteFileUrl('${file.delete_url
          }')">&times;</button>
            </li>`
        );
      }

      const finalReports = data.final_reports;
      const finalReportsList = $("#finalReportsList");
      finalReportsList.empty();

      for (const file of finalReports) {
        finalReportsList.append(
          `<li class="list-group-item">
<a href="${file.download}" target="_BLANK">${file.name} (${file.original})</a>
<button type="button" class="btn btn-outline-danger float-right" onclick="deleteFileUrl('${file.delete_url}')">&times;</button>
</li>`
        );
      }

      const attachments = data.attachments;
      const attachmentsList = $("#attachmentsList");
      attachmentsList.empty();

      for (const file of attachments) {
        attachmentsList.append(
          `<li class="list-group-item">
<a href="${file.download}" target="_BLANK">${file.name}</a>
<button type="button" class="btn btn-outline-danger float-right" onclick="deleteFileUrl('${file.delete_url}')">&times;</button>
</li>`
        );
      }
    },
    error: (xhr, textStatus, error) => {
      toastr.error(error);
    },
  });
}

function deleteFileUrl(url) {
  $.ajax(url, {
    method: "DELETE",
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
    },
    contentType: "application/json; charset=utf-8",

    success: (response) => {
      toastr.success("Eliminado exitosamente.");
      if (analysis) {
        refreshFileList(0, analysis);
      } else if (grouper) {
        refreshFileList(1, grouper);
      }
    },
    error: (err) => {
      toastr.error("Ha ocurrido un error.");
    },
  });
}

function getUrlByType(dom, urlName) {
  const dataset = dom.item[0].children[0].children[0].dataset;

  const analysisId = parseInt(dataset.analysis);
  const grouperId = parseInt(dataset.grouper);
  let url = "";

  // Url to update Stage is /review/stage/[type]/[pk]
  // where as Type is an int (0 or 1) where 0 indicates
  // AnalysisForm and 1 indicates Grouper where 0 indicates
  // Pk is the Primary Key of the object.
  if (analysisId) {
    url = Urls[urlName](0, analysisId);
  }

  if (grouperId) {
    url = Urls[urlName](1, grouperId);
  }

  return url;
}
