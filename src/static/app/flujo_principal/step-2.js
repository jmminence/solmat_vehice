var bd_correlative = 0;
var current_correlative = 0;
var organs;
var entryform;

function init_step_2() {
  var entryform_id = $("#entryform_id").val();

  var url = Urls.entryform_id(entryform_id);
  $.ajax({
    type: "GET",
    url: url,
  })
    .done(function (data) {
      $("#identification_group_list").html("");
      entryform = data.entryform;

      $(".showSummaryBtn").removeClass("hidden");
      $(".showReceptionFileBtn").removeClass("hidden");
      $(".showAttachedFilesBtn").removeClass("hidden");
    })
    .fail(function () {
      console.log("Fail");
    });

  var table = $("#identifications").DataTable({
    rowId: "id",
    columnDefs: [
      {
        width: "3%",
        targets: 0,
        className: "details-control",
        orderable: false,
        data: null,
        render: function (data, type, row, meta) {
          return `<i class="fa fa-chevron-right fa-fx fa-2x control-table" data-ident="${row.id}"></i>`;
        },
      },
      {
        width: "3%",
        targets: 1,
        orderable: false,
        data: "correlative",
        className: "correlative-text",
        render: function (data, type, row, meta) {
          return `${data ? data : ""}`;
        },
      },
      {
        width: "15%",
        targets: 2,
        orderable: false,
        data: "cage",
        render: function (data, type, row, meta) {
          return `<input name="cage" class="form-control-table ident-data" value="${
            data ? data : ""
          }" >`;
        },
      },
      {
        width: "15%",
        targets: 3,
        orderable: false,
        data: "group",
        render: function (data, type, row, meta) {
          return `<input name="group" class="form-control-table ident-data" value="${
            data ? data : ""
          }" >`;
        },
      },
      {
        width: "20%",
        targets: 4,
        orderable: false,
        data: "extra_features_detail",
        render: function (data, type, row, meta) {
          return `<textarea style="resize:none;" name="extra_features_detail" class="form-control-table ident-data" rows="1" >${
            data ? data : ""
          } </textarea>`;
        },
      },
      {
        width: "8%",
        targets: 5,
        orderable: false,
        data: "client_case_number",
        render: function (data, type, row, meta) {
          return `<input name="client_case_number" class="form-control-table ident-data" value="${
            data ? data : ""
          }" >`;
        },
      },
      {
        width: "5%",
        targets: 6,
        orderable: false,
        data: "weight",
        render: function (data, type, row, meta) {
          return `<input name="weight" class="form-control-table ident-data" type="number" step="0.1" min="0" value="${
            data ? data : "0"
          }" >`;
        },
      },
      {
        width: "3%",
        targets: 7,
        orderable: false,
        data: "is_optimum",
        render: function (data, type, row, meta) {
          if (data === false) {
            return `<input type="checkbox" style="margin-top:10%" name="is_optimum" class="form-control-table ident-data checkbox-2x">`;
          }
          return `<input type="checkbox" style="margin-top:10%" name="is_optimum" class="form-control-table ident-data checkbox-2x" checked>`;
        },
      },
      {
        width: "20%",
        targets: 8,
        orderable: false,
        data: "observation",
        render: function (data, type, row, meta) {
          return `<textarea name="observation" class="form-control-table ident-data" rows="1">${
            data ? data : ""
          } </textarea>`;
        },
      },
      {
        width: "3%",
        targets: 9,
        orderable: false,
        data: "quantity",
        render: function (data, type, row, meta) {
          return `<input id="amount_${
            row.id
          }" name="quantity" class="form-control-table amount" type="number" data-ident="${
            row.id
          }" value="${data ? data : "0"}" min="${data ? data : ""}">`;
        },
      },
      {
        width: "3%",
        targets: 10,
        orderable: false,
        data: null,
        render: function (data, type, row, meta) {
          return `<button class="btn btn-danger deleteIdent" type="button" data-ident="${row.id}"><i class="fa fa-trash fa-fx"></i></button>`;
        },
      },
    ],
    info: false,
    paging: false,
    searching: false,
    order: [[1, "asc"]],
    autoWidth: false,
    fixedHeader: {
      header: false,
      footer: false,
    },
  });

  var url = Urls.list_identification(entryform_id);
  $.ajax({
    type: "GET",
    url: url,
  })
    .done(function (data) {
      organs = data.data.organs;
      data.data.ident.forEach((element) => {
        if (!element.deleted) {
          addRow(element);
        }
        current_correlative = Math.max(
          element.correlative,
          current_correlative
        );
      });
      bd_correlative = current_correlative;
    })
    .fail(function () {
      console.log("Fail");
    });

  function format(dataRow) {
    let data = retrieveDataRow(dataRow);
    var id = data.id;
    var table_id = `units-table-${id}`;
    var contador_id = `contador-${id}`;
    var correlative_checked = "";
    if (data.samples_are_correlative) correlative_checked = "checked";
    var table_template = `
      <div class="row justify-content-center">
        <div class="switch-div form-group pl-2 pt-2">
          <input type="checkbox" id="correlative-${id}" class="switch2 correlative" ${correlative_checked} />
          <label for="correlative-${id}" class="font-medium-1 text-bold-600 ml-1">Un tubo corresponde a un pez</label>
        </div>
      </div>
      <div class="row pull-left">
        <div class="pl-0 col-sm-12">
          <button type="button" class="btn btn-sm btn-light" onclick="selectAllUnitsByIdentification(${id}, 1)"><i class="fa fa-check-square-o"></i> Seleccionar unidades</button>
          <button type="button" class="btn btn-sm btn-light" onclick="selectAllUnitsByIdentification(${id}, 0)"><i class="fa fa-square-o"></i> Deseleccionar unidades</button>
          <span class="badge badge-secondary contador_seleccion" id="${contador_id}">Tienes 0 unidades seleccionadas de 0 identificaciones</span>
        </div>
      </div>
      
      <table class='table w-100 table-unit' id="main-${table_id}">
      <thead>
      <th style="width:5%"></th> 
      <th style="width:5%">#</th> 
      <th>Tipo</th> 
      <th style="width: 65%">Órganos</th> 
      <th>Eliminar</th> 
      </thead>
      <div id="${table_id}_loading" class="text-center">
      Cargando ...
      </div>
      <tbody id="${table_id}">
      </tbody>
      </table>
      <table class='table w-100'>
      <thead>
      <th style="width:20%">Pool</th>
      <th>Organos</th>
      <th style="width:10%">Opciones</th>
      </thead>
      <tbody id="pool_${id}">
      </tbody>
      </table>
      <button type="button" data-id="${id}" class="btn btn-primary open-poolModal" data-toggle="modal" data-target="#poolModal">Agregar Pool</button> 
    `;
    var url = Urls.list_units(id);
    $.ajax({
      type: "GET",
      url: url,
    })
      .done(function (response) {
        $(`#${table_id}_loading`).remove();
        $(".switchery").remove();
        var elems = $(".switch2");
        $.each(elems, function (key, value) {
          new Switchery($(this)[0], {
            className: "switch2 switchery switchery-default",
          });
        });
        $.each(response.units, function (_, unit) {
          let rows = addUnitTemplate({
            ident_id: id,
            id: unit.id,
            entry_format: entryform.entry_format[1],
            organs: organs,
            unit_correlative: unit.correlative,
          });
          $(`#${table_id}`).append(rows);
          $(`#select-${id}-${unit.id}`).select2({
            templateResult: formatResultData,
            tags: false,
          });
          $.each(unit.organs, function (_, org) {
            selectOrgansWithConditions(
              org.id,
              org.name,
              id,
              $(`#select-${id}-${unit.id}`),
              false,
              false
            );
          });
        });
      })
      .fail(function () {
        console.log("Fail");
      });

      $.ajax({
        type: "GET",
        url: Urls.Pools(id),
      })
        .done(function (response){
          response.data.forEach(data => {
            addPoolRow(data)
          })
        })

    return table_template;
  }

  function addRow(data) {
    let index = table.rows()[0].length;
    table.row.add(data).draw();
  }

  // Add event listener for opening and closing details
  $("#identifications tbody").on("click", "td.details-control", function () {
    var tr = $(this).closest("tr");
    var icon = $($(this).children()[0]);
    var row = table.row(tr);

    if (row.child.isShown()) {
      // This row is already open - close it
      row.child.hide();

      icon.removeClass("fa-chevron-down");
      icon.addClass("fa-chevron-right");
      tr.removeClass("shown");
    } else {
      // Open this row
      row.child(format(row)).show();

      icon.removeClass("fa-chevron-right");
      icon.addClass("fa-chevron-down");
      tr.addClass("shown");
      let ident_id = tr.attr("id");
    }
  });

  $("#addIdent").on("click", function () {
    current_correlative += 1;
    var url = Urls.new_identification(entryform_id, current_correlative);
    let response;
    $.ajax({
      type: "POST",
      url: url,
      async: false,
    })
      .done(function (data) {
        addRow({
          id: data.obj.id,
          correlative: data.obj.correlative,
        });
      })
      .fail(function () {
        return false;
      });
  });

  $(document).on("click", ".deleteIdent", function () {
    var row = table.row($(this).parents("tr"));
    var url = Urls.remove_identification($(this).data("ident"));
    swal({
      title: "Desea eliminar la identificación?",
      text: "Esta acción es permanente!",
      icon: "warning",
      showCancelButton: true,
      buttons: {
        cancel: {
          // text: "{{request.lang.cancel_case}}",
          value: null,
          visible: true,
          className: "btn-danger",
          closeModal: true,
        },
        confirm: {
          // text: "{{request.lang.next}}",
          value: true,
          visible: true,
          className: "",
          closeModal: true,
        },
      },
    }).then((isConfirm) => {
      if (isConfirm) {
        remove_correlative = row.data().correlative;
        if (remove_correlative <= bd_correlative) {
          // OCULTAR EN BD ===> deleted = True
          $.ajax({
            type: "GET",
            url: url,
          })
            .done(function (data) {
              if (data.ok) {
                row.remove().draw();
                toastr.success(
                  "Identificación eliminada exitosamente.",
                  "Listo!"
                );
              } else {
                if (data.message == "CASSETTES") {
                  toastr.error(
                    "No ha sido posible eliminar la identificación, tiene Cassettes creados.",
                    "Ups!"
                  );
                } else {
                  toastr.error(
                    "No ha sido posible eliminar la identificación, intente nuevamente.",
                    "Ups!"
                  );
                }
              }
            })
            .fail(function () {
              console.log("Fail");
            });
        } else {
          current_correlative = current_correlative - 1;
          table.rows().every(function (rowIdx, tableLoop, rowLoop) {
            var d = this.data();
            if (remove_correlative < d.correlative) {
              let data = retrieveDataRow(this);
              data.correlative--;
              this.data(data).draw();
            }
          });
        }
      }
    });
  });

  $(document).on("click", ".unit-delete", function (e) {
    let id = $(this).data("id");
    let ident_id = $(this).data("ident");
    swal({
      title: "Desea eliminar la unidad?",
      text: "Esta acción es permanente!",
      icon: "warning",
      showCancelButton: true,
      buttons: {
        cancel: {
          // text: "{{request.lang.cancel_case}}",
          value: null,
          visible: true,
          className: "btn-danger",
          closeModal: true,
        },
        confirm: {
          // text: "{{request.lang.next}}",
          value: true,
          visible: true,
          className: "",
          closeModal: true,
        },
      },
    }).then((isConfirm) => {
      if (isConfirm) {
        let url = Urls.remove_unit(id);
        $.ajax({
          type: "POST",
          url: url,
          async: false,
        })
          .done(function (data) {
            if (data.ok) {
              let amount_control = $(`#amount_${ident_id}`);
              let new_value = amount_control.val() - 1;
              amount_control[0].min = new_value;
              amount_control[0].defaultValue = new_value;
              amount_control.val(new_value);
              saveIdentification(ident_id);
              $("#unit-" + ident_id + "-" + id).remove();
              let id_unit = "";
              $(`#units-table-${ident_id} .unit-correlative`).each(function (
                index,
                value
              ) {
                let indice = "" + (index + 1);
                if ($(this).val() != indice) {
                  $(this).val(indice);
                  id_unit = $(this).attr("id");
                }
              });
              if (id_unit != "") {
                $(`#${id_unit}`).trigger("change");
              }
              toastr.success("Unidad eliminada exitosamente.", "Listo!");
            } else {
              if (data.message == "CASSETTES") {
                toastr.error(
                  "No ha sido posible eliminar la unidad, tiene Cassettes creados.",
                  "Ups!"
                );
              } else {
                toastr.error(
                  "No ha sido posible eliminar la unidad, intente nuevamente.",
                  "Ups!"
                );
              }
            }
          })
          .fail(function () {
            toastr.error(
              "No ha sido posible eliminar la unidad, intente nuevamente.",
              "Ups!"
            );
          });
      }
    });
  });

  $(document).on("change", ".form-control-table.amount", function (e, param1) {
    lockScreen(1);
    if (this.defaultValue == this.value) return;

    var direction = parseInt(this.defaultValue) < parseInt(this.value);

    var id = $(this).data("ident");
    let table_id = `units-table-${id}`;
    if (direction) {
      let data_saved = false;

      for (
        let i = parseInt(this.defaultValue) + 1;
        i <= parseInt(this.value);
        i++
      ) {
        let result_ident = saveIdentification(id);

        if (result_ident.ok) {
          let last_tr_pos = parseInt(this.defaultValue) - 1;
          let res = getUnits(id);

          if (res.ok) {
            let units_correlatives = [];
            res.units.forEach(function (u) {
              units_correlatives.push(u.correlative);
            });
            let max_corr =
              units_correlatives.length > 0
                ? Math.max(...units_correlatives)
                : 0;
            let result_unit = createUnit(id, max_corr + 1);

            if (result_unit.ok) {
              let unit = result_unit.unit;

              let rows = addUnitTemplate({
                ident_id: unit.identification,
                id: unit.id,
                entry_format: entryform.entry_format[1],
                organs: organs,
                unit_correlative: unit.correlative,
              });

              $(`#${table_id}`).append(rows);

              $(`#select-${id}-${unit.id}`).select2({
                templateResult: formatResultData,
                tags: false,
              });

              data_saved = true;
            }
          }
        }
      }
      if (data_saved) {
        this.defaultValue = this.value;
      }
    } else {
      this.value = this.defaultValue;
    }
    lockScreen(0);
  });

  $(document).on("select2:selecting", ".organs", function (e) {
    e.preventDefault();

    let new_id = `${e.params.args.data.id}`;
    let new_value = e.params.args.data.text;
    let ident_id = e.target.id.split("-")[1];
    let select = e.target;

    selectOrgansWithConditions(new_id, new_value, ident_id, $(select));
    // saveUnitsByIdentification(ident_id)
  });

  $(document).on("select2:unselect", ".organs", function (e) {
    if (e.params.data.id.search("-") != -1) {
      e.params.data.element.remove();
    }
    let ident_id = e.target.id.split("-")[1];
    let response = saveUnitsByIdentification(ident_id);
    if (response.message == "CASSETTES") {
      toastr.error(
        "No ha sido posible eliminar uno de los organos, tiene Cassettes creados.",
        "Ups!"
      );
      location.reload();
    }
  });

  $(document).on("change", ".correlative", function (e) {
    let id = e.target.id.split("-")[1];
    if (e.target.checked) {
      swal({
        title: "Organos en correlativos",
        text: "Se eliminarán los órganos repetidos",
        icon: "warning",
        showCancelButton: true,
        buttons: {
          cancel: {
            value: null,
            visible: true,
            className: "btn-danger",
            closeModal: true,
          },
          confirm: {
            value: true,
            visible: true,
            className: "",
            closeModal: true,
          },
        },
      }).then((isConfirm) => {
        if (!isConfirm) {
          e.target.click();
          return;
        }
        resetOrgansOptions(id, true);
        saveIdentification(id);
        saveUnitsByIdentification(id);
      });
    } else {
      resetOrgansOptions(id, false);
      saveIdentification(id);
      saveUnitsByIdentification(id);
    }
  });

  $(document).on("blur", ".ident-data", function () {
    let id = $(this).parent().parent().attr("id");
    saveIdentification(id);
  });

  $(document).on("change", ".unit-correlative", function (e, param1) {
    let correlative_input = this;
    let ident_id = $(correlative_input).attr("id").split("-")[1];
    let current_unit_id = $(correlative_input).attr("id").split("-")[2];

    let current_correlative_value = correlative_input.value;
    let current_default_value = correlative_input.defaultValue;

    let correlative_switch_option = $("#correlative-" + ident_id).is(
      ":checked"
    );

    if (correlative_switch_option) {
      if (checkDuplicatedOrgansInSameCorrelative(ident_id, current_unit_id)) {
        correlative_input.value = current_default_value;
        alertDuplicatedOrgansInSameCorrelative();
      } else {
        correlative_input.defaultValue = current_correlative_value;
        saveUnitsByIdentification(ident_id);
      }
    } else {
      correlative_input.defaultValue = current_correlative_value;
      saveUnitsByIdentification(ident_id);
    }
  });
}

$(document).on("change", ".unit-select", function () {
  if ($(".table-unit .unit-select:checked").length > 0) {
    let table_ids = [];
    $(".table-unit .unit-select:checked").each(function (i, v) {
      let ident_id = $(this).closest("tr").attr("id").split("-")[1];
      if (table_ids.indexOf(ident_id) == -1) {
        table_ids.push(ident_id);
      }
    });
    $(".contador_seleccion").html(
      `Tienes ${
        $(".table-unit .unit-select:checked").length
      } unidades seleccionadas de ${table_ids.length} identificaciones`
    );
  } else {
    $(".contador_seleccion").html(
      `Tienes 0 unidades seleccionadas de 0 identificaciones`
    );
  }
});

function alertDuplicatedOrgansInSameCorrelative() {
  swal({
    title: "Información",
    text:
      "No ha sido posible realizar el cambio debido a que existe duplicidad de órganos en muestra correlativa.",
    icon: "warning",
    showCancelButton: false,
  });
}

function checkDuplicatedOrgansInSameCorrelative(
  ident_id,
  unit_id,
  organs_selected = false
) {
  let current_correlative = $("#input-" + ident_id + "-" + unit_id).val();
  if (!organs_selected) {
    var organs_selected = $("#select-" + ident_id + "-" + unit_id).val();
  }

  let organs_validator = false;
  $.each($("#units-table-" + ident_id + " tr"), function (i, tr) {
    let tr_unit_id = $(tr).attr("id").split("-")[2];
    let tr_correlative_value = $(tr).find(".unit-correlative").val();
    if (unit_id != tr_unit_id && current_correlative == tr_correlative_value) {
      let tr_organs_selected = $(tr).find(".organs").val();
      if (organs_selected.some((r) => tr_organs_selected.indexOf(r) >= 0)) {
        organs_validator = true;
        return false;
      }
    }
  });
  return organs_validator;
}

function addUnitTemplate(data) {
  var unitTemplate = document.getElementById("unit_template").innerHTML;

  var templateFn = _.template(unitTemplate);
  var templateHTML = templateFn(data);
  return templateHTML;
}

function retrieveDataRow(row) {
  var data = row.data();

  $.each($(`#${data.id} .form-control-table`), function (i, v) {
    if ($(v).attr("type") == "checkbox") {
      data[v.name] = v.checked ? 1 : 0;
    } else {
      data[v.name] = v.value;
    }
  });

  return data;
}

/*** Select organs based on switches values (organs for all and correlative samples) ***/
function selectOrgansWithConditions(
  new_id,
  new_value,
  ident_id,
  select,
  loop_by_units_selected = true,
  force_save_units = true
) {
  let organs_switch_option;
  if (loop_by_units_selected) {
    organs_switch_option =
      $(".table-unit .unit-select:checked").length > 0 ? true : false;
  } else {
    organs_switch_option = false;
  }

  let correlative_switch_option = $("#correlative-" + ident_id).is(":checked");

  if (organs_switch_option) {
    // $.each( $("#units-table-"+ident_id+" tr"), function (i, v) {
    let idents_to_save = [];
    $.each($(".table-unit .unit-select:checked"), function (i, v) {
      let tr = $(this).closest("tr");
      let checkbox = tr.find(".unit-select").is(":checked");
      let select = tr.find(".organs");
      let unit_id = select.attr("id").split("-")[2];
      let ident_id = select.attr("id").split("-")[1];
      let values = select.val();

      if (checkbox) {
        if (!correlative_switch_option) {
          new_aux_id = `${new_id}-${Math.random()}`;
          select.append(`<option value="${new_aux_id}">${new_value}</option>`);
          values.push(new_aux_id);
          select.val(values);
          select.trigger("change");
        } else {
          values.push(new_id);
          if (
            !checkDuplicatedOrgansInSameCorrelative(ident_id, unit_id, values)
          ) {
            select.val(values);
            select.trigger("change");
          } else {
            alertDuplicatedOrgansInSameCorrelative();
          }
        }
      }
      idents_to_save.push(ident_id);
    });

    if (force_save_units) {
      $.each($.unique(idents_to_save), function (_, ident) {
        saveUnitsByIdentification(ident);
      });
    }
  } else {
    let values = select.val();
    let unit_id = select.attr("id").split("-")[2];
    if (!correlative_switch_option) {
      new_id = `${new_id}-${Math.random()}`;
      select.append(`<option value="${new_id}">${new_value}</option>`);
      values.push(new_id);
      select.val(values);
      select.trigger("change");
    } else {
      values.push(new_id);
      if (!checkDuplicatedOrgansInSameCorrelative(ident_id, unit_id, values)) {
        select.val(values);
        select.trigger("change");
      } else {
        alertDuplicatedOrgansInSameCorrelative();
      }
    }

    if (force_save_units) {
      saveUnitsByIdentification(ident_id);
    }
  }
}

function resetOrgansOptions(id, correlative) {
  var unitTemplate = document.getElementById("organos_options").innerHTML;
  var templateFn = _.template(unitTemplate);
  var templateHTML = templateFn({ organs });

  $.each($(`.organs-${id}`), function (i, v) {
    let select = $(v);
    let values = select.val();
    let selected = [];

    values.forEach((element) => {
      let x = element.split("-")[0];
      if (selected.indexOf(x) == -1) {
        selected.push(x);
      } else {
      }
    });

    select.html(templateHTML);

    if (correlative) {
      select.val(selected).trigger("change");
    } else {
      let selected_unique = [];
      values.forEach((x) => {
        element = x.split("-")[0];
        let new_id = `${element}-${Math.random()}`;
        let new_value = select.find("option[value='" + element + "']").text();
        select.append(`<option value="${new_id}">${new_value}</option>`);
        selected_unique.push(new_id);
      });
      select.val(selected_unique).trigger("change");
    }
  });
}

function formatResultData(data) {
  if (data.selected) {
    return null;
  }
  return data.text;
}

function validate_step_2() {
  let sucess = 1;

  if ($("#identifications").DataTable().data().rows().count() == 0) {
    toastr.error(
      "Para continuar debe ingresar las identificaciones.",
      "Error",
      {
        positionClass: "toast-top-full-width",
        containerId: "toast-bottom-full-width",
      }
    );
    return false;
  }

  let amounts_greather_than_zero = true;
  $(".amount").each(function (_, e) {
    if (e.value == 0) {
      amounts_greather_than_zero = false;
      return false;
    }
  });

  if (!amounts_greather_than_zero) {
    toastr.error(
      "Para continuar la cantidad de unidades en las identificaciones ingresadas deben ser mayor a 0.",
      "Error",
      {
        positionClass: "toast-top-full-width",
        containerId: "toast-bottom-full-width",
      }
    );
    return false;
  }

  let organs_more_than_zero = true;
  $(".organs").each(function (_, e) {
    if ($(this).val().length == 0) {
      organs_more_than_zero = false;
      return false;
    }
  });

  if (!organs_more_than_zero) {
    toastr.error(
      "Para continuar es requerido que seleccione órganos en cada unidad declarada.",
      "Error",
      {
        positionClass: "toast-top-full-width",
        containerId: "toast-bottom-full-width",
      }
    );
    return false;
  }

  return sucess;
}

function openOrgansKeypad() {
  var organs_keypad_template = document.getElementById("organs_keypad")
    .innerHTML;
  var templateFn = _.template(organs_keypad_template);

  var data = {
    organs: organs,
  };

  var templateHTML = templateFn({ data });
  $("#organ_table_keypad_body").html(templateHTML);
  $("#organ_table_keypad").modal("show");
  $("#switch_keypad").checkboxpicker();
}

var waitForEl = function (selector, callback) {
  if ($(selector).length) {
    callback();
  } else {
    setTimeout(function () {
      waitForEl(selector, callback);
    }, 500);
  }
};

function AddOrgansFromKeypadToUnits(add) {
  let organs_selected_from_keypad = [];
  $(".keypad-organ-selector").each(function (e) {
    let span = $(this).find(".organ_counter")[0];
    let organ_id = $(this).data("id");
    let organ_name = $(this).data("name");
    let organ_amount = parseInt($(span).text());

    if (organ_amount > 0) {
      for (let i = 0; i < organ_amount; i++) {
        organs_selected_from_keypad.push([organ_id, organ_name]);
      }
    }
  });

  if (organs_selected_from_keypad.length > 0) {
    $.each($("#identifications .table-idents tr"), function (i, tr) {
      let row = $("#identifications").DataTable().row(tr);

      if (!row.child.isShown()) {
        $(tr).find(".details-control").first().click();
        $(tr).addClass("shown");
      }

      let ident_id = $(tr).attr("id");
      let units_tbody_trs = "units-table-" + ident_id + " tr";
      let units_edited = false;

      waitForEl("#" + units_tbody_trs, function () {
        $("#" + units_tbody_trs).each(function (_, s_tr) {
          let unit_tr_id = $(s_tr).attr("id");
          let unit_id = unit_tr_id.split("-")[2];
          let unit_selection = $(s_tr).find(".unit-select")[0];

          if ($(unit_selection).is(":checked")) {
            units_edited = true;
            if (add) {
              $.each(organs_selected_from_keypad, function (index, value) {
                selectOrgansWithConditions(
                  value[0],
                  value[1],
                  ident_id,
                  $("#select-" + ident_id + "-" + unit_id),
                  false,
                  false
                );
              });
            } else {
              $.each(organs_selected_from_keypad, function (index, value) {
                let aux_val = $("#select-" + ident_id + "-" + unit_id).val();
                let new_values = [];
                let deleted = false;
                for (let org of aux_val) {
                  if (!org.startsWith(value[0])) {
                    new_values.push(org);
                  } else if (org.startsWith(value[0]) && deleted) {
                    new_values.push(org);
                  } else if (org.startsWith(value[0]) && !deleted) {
                    deleted = true;
                  }
                }
                $("#select-" + ident_id + "-" + unit_id)
                  .val(new_values)
                  .trigger("change");
              });
            }
          }
        });
      });

      if (units_edited) {
        saveUnitsByIdentification(ident_id);
      }
    });
  }

  $("#organ_table_keypad").modal("hide");
}

function createUnit(identification_id, correlative) {
  let url = Urls.create_unit(identification_id, correlative);
  let response;
  $.ajax({
    type: "POST",
    url: url,
    async: false,
  })
    .done(function (data) {
      response = data;
    })
    .fail(function () {
      reponse = { ok: 0 };
    });

  return response;
}

function saveIdentification(id) {
  let url = Urls.save_new_identification(id);
  let ident = retrieveDataRow(
    $("#identifications")
      .DataTable()
      .row($("#" + id))
  );
  ident["samples_are_correlative"] = $("#correlative-" + id).is(":checked")
    ? 1
    : 0;

  let response;
  $.ajax({
    type: "POST",
    url: url,
    async: false,
    data: ident,
  })
    .done(function (data) {
      response = data;
    })
    .fail(function () {
      reponse = { ok: 0 };
    });
  return response;
}

function saveUnitsByIdentification(ident_id) {
  let units = [];
  $.each($("#units-table-" + ident_id + " tr"), function (i, tr) {
    let unit = {};
    unit["id"] = $(tr).attr("id").split("-")[2];
    unit["correlative"] = $("#input-" + ident_id + "-" + unit["id"]).val();
    unit["organs"] = $("#select-" + ident_id + "-" + unit["id"]).val();
    units.push(unit);
  });

  let url = Urls.save_units();
  let response;
  $.ajax({
    type: "POST",
    url: url,
    async: false,
    data: { units: JSON.stringify(units) },
  })
    .done(function (data) {
      response = data;
    })
    .fail(function () {
      reponse = { ok: 0 };
    });
  return response;
}

function getUnits(ident_id) {
  let url = Urls.list_units(ident_id);
  let response;
  $.ajax({
    type: "GET",
    url: url,
    async: false,
  })
    .done(function (data) {
      response = data;
    })
    .fail(function () {
      response = { ok: 0 };
    });
  return response;
}

function selectAllUnits(opt) {
  if (opt == 1) {
    $.each($("#identifications .table-idents tr"), function (i, tr) {
      var row = $("#identifications").DataTable().row(tr);

      if (!row.child.isShown()) {
        $(tr).find(".details-control").first().click();
        $(tr).addClass("shown");
      }

      let ident_id = $(tr).attr("id");
      let units_tbody_trs = "units-table-" + ident_id + " tr";

      waitForEl("#" + units_tbody_trs, function () {
        $("#" + units_tbody_trs + " .unit-select").prop("checked", true);
        $(".unit-select").trigger("change");
      });
    });
  } else {
    $.each($("#identifications .table-idents tr"), function (i, tr) {
      var row = $("#identifications").DataTable().row(tr);

      if (!row.child.isShown()) {
        $(tr).find(".details-control").first().click();
        $(tr).addClass("shown");
      }

      let ident_id = $(tr).attr("id");
      let units_tbody_trs = "units-table-" + ident_id + " tr";

      waitForEl("#" + units_tbody_trs, function () {
        $("#" + units_tbody_trs + " .unit-select").prop("checked", false);
        $(".unit-select").trigger("change");
      });
    });
  }
}

function selectAllUnitsByIdentification(id, opt) {
  let units_tbody_trs = "units-table-" + id + " tr";
  if (opt == 1) {
    waitForEl("#" + units_tbody_trs, function () {
      $("#" + units_tbody_trs + " .unit-select").prop("checked", true);
    });
  } else {
    let units_tbody_trs = "units-table-" + id + " tr";

    waitForEl("#" + units_tbody_trs, function () {
      $("#" + units_tbody_trs + " .unit-select").prop("checked", false);
    });
  }
  $(".unit-select").trigger("change");
}

$(document).on("click", ".keypad-organ-selector", function () {
  let span = $(this).find("span")[0];
  let current_value = parseInt($(span).text());

  if ($("#switch_keypad").is(":checked")) {
    $(span).text(current_value + 1);
  } else {
    if (current_value > 0) {
      $(span).text(current_value - 1);
    }
  }
});

$(document).on('show.bs.modal', '#poolModal', function (e) {
  var identification_id = e.relatedTarget.dataset.id
  var pool_id = e.relatedTarget.dataset.pool
  identification_title_pool = document.getElementsByClassName('identification_title_pool')[0]
  poolName = document.getElementById("poolName");
  poolName.value = ""
  poolName.disabled = false;

  $.ajax({
    type: "GET",
    url: Urls.pool_list_organs(identification_id),
    success: function(data){
        data = JSON.parse(data.context);
        if (data.identification.group != "" && data.identification.group != null) {
          identification_title_pool.textContent = `${data.identification.cage}(${data.identification.group})`
        }else{
          identification_title_pool.textContent = `${data.identification.cage}`
        }
        identification_title_pool.id = identification_id
        modalData(data,pool_id)
    }
  });
});


function modalData(data,pool_id) {
  clearPoolHtml()
  units_body = document.getElementById('units_body')
  data.units.forEach(unit => {
    html = `<div id="pool_unit_${unit.unit_id}" class="d-block mb-1">
      <p class="h6">Unidad N°${unit.correlative}</p>
      <div class="d-flex" id="pool_organs_${unit.unit_id}" style="overflow-y:auto;">
      </div>
    </div>`
    units_body.insertAdjacentHTML( 'beforeend', html );

    organs_div = document.getElementById("pool_organs_"+unit.unit_id)
    unit.organs.forEach(organ => {
      organ_button = `<div class="btn-group-toggle" style="margin:5px" data-toggle="buttons">
      <label class="btn btn-secondary checkbox_button">
        <input id="organ_${organ.organ_unit_id}" value="${organ.organ_unit_id}" type="checkbox" class="checkbox" checked autocomplete="off"> ${organ.organ}
      </label>
    </div>`
      organs_div.insertAdjacentHTML( 'beforeend', organ_button );
    })
  })

  if (pool_id != undefined) {
    poolName = document.getElementById("poolName");
    poolName.disabled = true;
    $.ajax({
      type: "GET",
      url: Urls.pool_id(data.identification.id),
      data: {"pool":pool_id},
      success: function(data){
        pool = data.pool;
        poolName = document.getElementById("poolName");
        poolName.value = pool.name;

        savePoolButton = document.getElementById("savePoolButton")
        savePoolButton.setAttribute("onclick", `savePool(${pool.id})`)

        organ_units = data.organ_units;
        organ_units.forEach(organ_unit_id => {
          organ_button = document.getElementById(`organ_${organ_unit_id}`).parentElement;
          organ_button.setAttribute("class", "btn btn-secondary checkbox_button active btn-warning");
        })
      }
    });
  }else{
    savePoolButton = document.getElementById("savePoolButton")
    savePoolButton.setAttribute("onclick", "savePool()")
  }
}

function clearPoolHtml(){
  units_body = document.getElementById('units_body')
  units_body.innerHTML = ""
}

function savePool(pool=null){
  organs = document.getElementsByClassName("checkbox_button");
  identification_id = document.getElementsByClassName("identification_title_pool")[0].id
  poolName = document.getElementById("poolName").value
  organs_selected = [];

  Array.from(organs).forEach(organ => {
    if(organ.classList.contains("active")){
      organs_selected.push(parseInt(organ.children[0].value))
    }
  });

  if (organs_selected.length > 0 && poolName != "") {
    if (pool != null) {
      $.ajax({
        type: "PUT",
        url: Urls.edit_pool(pool),
        data: JSON.stringify({
          "identification_id":identification_id,
          "name":poolName,
          "organs_selected":organs_selected
        }),
        contentType: "application/json",
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
        },
        success: function(data){
          select_pool = document.getElementById("select-"+pool)
          data.organ_unit_removed.forEach(organ_unit => {
            option_pool = document.getElementById(`option-${pool}-${organ_unit}`);
            option_pool.remove();
          })

          data.organ_unit_adds.forEach(organ_unit => {
            var option = document.createElement("option");
            option.id = `option-${pool}-${organ_unit.id}`
            option.value = organ_unit.id;
            option.text =`${organ_unit.organ}(${organ_unit.correlativo})`;
            option.selected = true;
            select_pool.appendChild(option);
          })

          select_pool.trigger('change');
        }
      });
    }else{
      $.ajax({
        type: "POST",
        url: Urls.createPool(),
        data:{
          "identification_id":identification_id,
          "name":poolName,
          "organs_selected":organs_selected
        },
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
        },
        success: function(data){
          data = data.context
          addPoolRow(data)
        }
      });
    }
  }
}

function addPoolRow(data){
  pool = data.pool
  organs_list = data.pool_organunit_list

  tableBody = document.getElementById("pool_"+pool.identification)
  row = tableBody.insertRow()
  row.setAttribute("id", "rowPool_"+pool.id);

  for (i = 0; i < 3; i++) {
    switch(i){
      case 0:
        var newCell = row.insertCell(0);
        var newText = document.createTextNode(pool.name);
        newCell.appendChild(newText);

        break;
      
      case 1:
        var newCell = row.insertCell(1);
        var select = document.createElement("select");
        select.id = "select-"+pool.id;
        select.multiple = true;
        select.setAttribute("class","form-control-table form-control poolOrgansSelect")
        select.setAttribute("style","width:100%")
        select.setAttribute('disabled', true);

        organs_list.forEach(organ => {
          var option = document.createElement("option");
          option.id = `option-${pool.id}-${organ.organunit_id}`
          option.value = organ.organunit_id;
          option.text =`${organ.organ}(${organ.correlativo})`;
          option.selected = true;
          select.appendChild(option);
        })
        newCell.appendChild(select);
      
        break;

      case 2:
        var newCell = row.insertCell(2);
        var editButton = `<button type="button" data-id="${pool.identification}" data-pool="${pool.id}" class="btn btn-warning mr-1 open-poolModal" data-toggle="modal" data-target="#poolModal"><i class="fa fa-pencil-square-o" aria-hidden="true"></i></button>`
        newCell.insertAdjacentHTML('beforeend', editButton);
        var deleteButton = `<button class="btn btn-danger" type="button" onclick="deletePool(${pool.id})"><i class="fa fa-trash fa-fx"></i></button>`
        newCell.insertAdjacentHTML('beforeend', deleteButton);
        
        break;
    }
  }
  $(".poolOrgansSelect").select2();
}

function deletePool(id){
  $.ajax({
    type: "POST",
    url: Urls.deletePool(id),
    success: function(data){
      row = document.getElementById("rowPool_"+data.data)
      row.remove()
    }
  })
}