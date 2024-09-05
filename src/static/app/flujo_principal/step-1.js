// Data Template
var organs;
var questionReceptionCondition;
var researches_json = {};

function init_step_1() {
  var url = Urls.entryform();
  $.ajax({
    type: "GET",
    url: url,
  })
    .done(function (data) {
      initialData(data);
      organs = data.organs;
      initialConf();
      loadData();
    })
    .fail(function () {
      console.log("Fail");
    });

  $(document).on("change", "#step_0 input", function () {
    formChanged = true;
  });

  $(document).on("change", "#step_0 textarea", function () {
    formChanged = true;
  });

  $.ajax({
    type: "GET",
    url: Urls.centers_list(),
  }).done((data) => {
    const centerDataList = $("#centers");
    for (const center of data) {
      const option = `<option value="${center}">`;
      centerDataList.append(option);
    }
  });

  function loadData() {
    var entryform_id = $("#entryform_id").val();
    var url = Urls.entryform_id(entryform_id);
    $.ajax({
      type: "GET",
      url: url,
    })
      .done(function (data) {
        var entryform = data.entryform;
        if (entryform.customer_id) {
          $("#customer_select").val(entryform.customer_id).trigger("change");
        }

        if (entryform.entryform_type_id) {
          if (entryform.entryform_type_id == 1) {
            $("#entryform_type_1").prop("checked", true);
          } else {
            $("#entryform_type_2").prop("checked", true);
          }
        }

        $("#fixtative_select").val(entryform.fixative_id).trigger("change");
        $("#observation").val(entryform.observation);
        $("#order_number_input").val(entryform.no_order);
        $("#request_number_input").val(entryform.no_request);
        $("#anamnesis_input").val(entryform.anamnesis);
        if (entryform.anamnesis  && entryform.anamnesis.length === 0) {
          $("#anamnesis_input").hide();
        } else {
          $("#anamnesis_input").show();
        }
        // $("#company_input").val(entryform.company);
        $("#center_input").val(entryform.center);
        $("#responsible_input").val(entryform.responsible);
        $("#transfer_order_input").val(entryform.transfer_order);
        $("#entryformat_select").val(entryform.entry_format).trigger("change");

        if (entryform.larvalstage_id) {
          $("#larvalstage_select")
            .val(entryform.larvalstage_id)
            .trigger("change");
        } else {
          $('#larvalstage_select option:contains("S/I")')
            .attr("selected", "selected")
            .trigger("change");
        }
        if (entryform.watersource_id) {
          $("#watersource_select")
            .val(entryform.watersource_id)
            .trigger("change");
        } else {
          $('#watersource_select option:contains("S/I")')
            .attr("selected", "selected")
            .trigger("change");
        }
        if (entryform.specie_id) {
          $("#specie_select").val(entryform.specie_id).trigger("change");
        } else {
          $('#specie_select option:contains("S/I")')
            .attr("selected", "selected")
            .trigger("change");
        }
        if (entryform.created_at) {
          $('[name="created_at"]').val(
            moment(entryform.created_at).format("DD/MM/YYYY HH:mm") || ""
          );
        } else {
          $('[name="created_at"]').val("");
        }
        if (entryform.sampled_at) {
          $('[name="sampled_at"]').val(
            moment(entryform.sampled_at).format("DD/MM/YYYY") || ""
          );
        } else {
          $('[name="sampled_at"]').val("");
        }

        if (entryform.sampled_at_hour) {
          $('[name="sampled_at_hour"]').val(
            moment(entryform.sampled_at_hour).format("hh:mm") || ""
          );
        } else {
          $('[name="sampled_at_hour"]').val("");
        }

        $("#created_at_submit").val(entryform.created_at);
        $("#sampled_at_submit").val(entryform.sampled_at);

        if (entryform.sampled_at_am_pm) {
          $("#sampled_at_am_pm").val(entryform.sampled_at_am_pm);
        }
      })
      .fail(function () {
        console.log("Fail");
      });
  }

  function initialData(data) {
    loadCustomers(data.customers);
    loadFixtatives(data.fixtatives);
    loadSpecies(data.species);
    loadLarvalStages(data.larvalStages);
    loadWaterSources(data.waterSources);
    loadLaboratories(data.laboratories);
  }

  function initialConf() {
    $("#datetime_created_at").datetimepicker({
      locale: "es",
      keepOpen: false,
      format: "DD/MM/YYYY HH:mm",
    });
    $("#datetime_created_at").on("dp.change", function (ev) {
      formChanged = true;
    });

    $("#datetime_sampled_at")
      .datetimepicker({
        locale: "es",
        keepOpen: false,
        format: "DD/MM/YYYY",
      })
      .on("dp.change", function (ev) {
        formChanged = true;
      });

    $("#datetime_sampled_at_hour")
      .datetimepicker({
        locale: "es",
        keepOpen: false,
        format: "hh:mm",
      })
      .on("dp.change", function (ev) {
        formChanged = true;
      });

    $("#customer_select")
      .select2({
        placeholder: "Seleccione un cliente",
      })
      .on("select2:select", function (e) {
        formChanged = true;
      });

    $("#center_select")
      .select2({
        placeholder: "Seleccione un Centro",
      })
      .on("select2:select", function (e) {
        formChanged = true;
      });

    $("#company_select")
      .select2({
        placeholder: "Seleccione un Empresa",
      })
      .on("select2:select", async function (e) {
        let data = await fetchCustomerCenters(e.params.data.id);

        if (data.length > 0) {
          // show select component
          $("#center_select")
            .select2({
              placeholder: "Seleccione un Centro",
            });
          $("#center_select").css("display", "block");
          $("#center_select").prop("disabled", false);
          $("#center_select").empty();
          $("#center_select").append(
            $("<option>", {
              value: '',
              text: '',
              selected: true //Placeholder active
            })
          );
          document.getElementById('company_type_center').style.display = 'block';
          document.getElementById('company_type_lab').style.display = 'none';
          $("#center_input").css("display", "none");
          $("#center_input").val('');

          data.forEach(customer_center => {
            $("#center_select").append(
              $("<option>", {
                value: customer_center.id,
                text: customer_center.center.name,
              })
            );
          });
        } else {
          // show input text component
          $("#center_input").css("display", "block");
          $("#center_input").prop("disabled", false);

          $("#center_select").empty();
          $("#center_select").append(
            $("<option>", {
              value: '',
              text: '', 
              selected: true //Placeholder active
            })
          );
          // document.getElementById('center_select').style.display = "none";
          // $("#center_select")
          //   .select2('destroy').hide();
          let $select2 = $('#center_select').select2();
          $select2.next('.select2-container').css('display', 'none');
          document.getElementById('company_type_center').style.display = 'none';
          document.getElementById('company_type_lab').style.display = 'block';
          $("#center_select").append(
              $("<option>", {
                  value: '',
                  text: '',
                  selected: true
              })
          );
        }

      });

    $("#fixtative_select")
      .select2({
        placeholder: "Porfavor seleccione un fijador",
      })
      .on("select2:select", function (e) {
        formChanged = true;
      });

    $("#specie_select")
      .select2({
        placeholder: "Porfavor seleccione una especie",
      })
      .on("select2:select", function (e) {
        formChanged = true;
      });

    $("#larvalstage_select")
      .select2({
        placeholder: "Porfavor seleccione un estadio desarrollo",
      })
      .on("select2:select", function (e) {
        formChanged = true;
      });

    $("#watersource_select")
      .select2({
        placeholder: "Porfavor seleccione una fuente de agua",
      })
      .on("select2:select", function (e) {
        formChanged = true;
      });
  }
}

$(document).on("click", "#saveStep1", function () {
  form_data = $("#step_0 :input").serialize();
  $.ajax({
    type: "POST",
    url: "/workform/1/save_step1",
    data: form_data,
  })
    .done(function (data) {
      if (data.ok) {
        formChanged = false;
        toastr.success("Se guardó satisfactoriamente", "");
      } else {
        formChanged = true;
        toastr.error("No se pudo guardar satisfactoriamente", "Aviso");
      }
    })
    .fail(function (data) {
      console.log("Fail");
    });
});

function validate_step_1() {
  let sucess = 1;

  if ($("#customer_select").val() == null || $("#customer_select").val() == "") {
    toastr.error("Para continuar debe seleccionar un cliente.", "Error", {
      positionClass: "toast-top-full-width",
      containerId: "toast-bottom-full-width",
    });
    return false;
  }

  if ($("#company_select").val() == null || $("#company_select").val() == "") {
    toastr.error("Para continuar debe seleccionar una empresa.", "Error", {
      positionClass: "toast-top-full-width",
      containerId: "toast-bottom-full-width",
    });
    return false;
  }

  if ($("#created_at").val() == "") {
    toastr.error(
      "Para continuar debe ingresar la fecha de repceción.",
      "Error",
      {
        positionClass: "toast-top-full-width",
        containerId: "toast-bottom-full-width",
      }
    );
    return false;
  }

  if ($("#entryformat_select").val() == "") {
    toastr.error(
      "Para continuar debe seleccionar el formato de ingreso.",
      "Error",
      {
        positionClass: "toast-top-full-width",
        containerId: "toast-bottom-full-width",
      }
    );
    return false;
  }

  if ($("#specie_select").val() == "") {
    toastr.error("Para continuar debe seleccionar la especie.", "Error", {
      positionClass: "toast-top-full-width",
      containerId: "toast-bottom-full-width",
    });
    return false;
  }

  if ($("#larvalstage_select").val() == "") {
    toastr.error("Para continuar debe seleccionar estadío.", "Error", {
      positionClass: "toast-top-full-width",
      containerId: "toast-bottom-full-width",
    });
    return false;
  }

  if ($("#watersource_select").val() == "") {
    toastr.error("Para continuar debe seleccionar fuente de agua.", "Error", {
      positionClass: "toast-top-full-width",
      containerId: "toast-bottom-full-width",
    });
    return false;
  }

  return sucess;
}

function splitArrayByChunkSize(arr, n) {
  var rest = arr.length % n,
    restUsed = rest,
    partLength = Math.floor(arr.length / n),
    result = [];

  for (var i = 0; i < arr.length; i += partLength) {
    var end = partLength + i,
      add = false;

    if (rest !== 0 && restUsed) {
      end++;
      restUsed--;
      add = true;
    }

    result.push(arr.slice(i, end));

    if (add) {
      i++;
    }
  }
  return result;
}

function loadCustomers(customers) {
  $.each(customers, function (i, item) {
    $("#customer_select").append(
      $("<option>", {
        value: item.id,
        text: item.name,
        "data-type-customer": item.type_customer,
      })
    );
    $("#company_select").append(
      $("<option>", {
        value: item.id,
        text: item.name,
        "data-type-customer": item.type_customer,
      })
    );
  });
}

function loadFixtatives(fixtatives) {
  $.each(fixtatives, function (i, item) {
    $("#fixtative_select").append(
      $("<option>", {
        value: item.id,
        text: item.name,
      })
    );
  });
}

function loadSpecies(species) {
  $.each(species, function (i, item) {
    $("#specie_select").append(
      $("<option>", {
        value: item.id,
        text: item.name,
      })
    );
  });
}

function loadLarvalStages(larvalStages) {
  $.each(larvalStages, function (i, item) {
    $("#larvalstage_select").append(
      $("<option>", {
        value: item.id,
        text: item.name,
      })
    );
  });
}

function loadWaterSources(waterSources) {
  $.each(waterSources, function (i, item) {
    $("#watersource_select").append(
      $("<option>", {
        value: item.id,
        text: item.name,
      })
    );
  });
}

function loadLaboratories(laboratories) {
  $.each(laboratories, function (i, item) {
    $("#laboratory_select").append(
      $("<option>", {
        value: item.id,
        text: item.name,
      })
    );
  });
}

$(document).on("click", ".showResearchPopover", function () {
  var id = $("#researches_select").val();
  swal(researches_json[id]);
});

async function fetchCustomerCenters(customer_id) {
  const response = await fetch(`api/customer/${customer_id}/centers`, {
    method: 'GET',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
    }
  });
  data = await response.json();
  return data;
}

function getCookie(name) {
  var cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    var cookies = document.cookie.split(";");
    for (var i = 0; i < cookies.length; i++) {
      var cookie = jQuery.trim(cookies[i]);
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(
          cookie.substring(name.length + 1)
        );
        break;
      }
    }
  }
  return cookieValue;
}