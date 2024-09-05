var data_step_2;
var patologos_list;
var previous_data_exists = false;

function init_step_2() {
  var entryform_id = $('#entryform_id').val();
  var url = Urls.entryform_id(entryform_id);

  $.ajax({
    type: "GET",
    url: url,
    async: false,
  })
  .done(function (data) {
    data_step_2 = data
    $('.showSummaryBtn').removeClass("hidden");
    $('.showAttachedFilesBtn').removeClass("hidden");
    $('.showShareBtn').addClass("hidden");
    $('.showLogBtn').addClass("hidden");
    $('.newAnalysisBtn').addClass("hidden");
    $('.newAnalysisBtn5').addClass("hidden");
     // fillSummary(data);
    if (data.entryform.analyses.length > 0){
      previous_data_exists = true;
    }
    initialData(data);
    loadData(data);
  })
  .fail(function () {
  })

  if ($('#exam_select').hasClass("select2-hidden-accessible")) {
    $('#exam_select').select2('destroy');
    $('#exam_select').off('select2:select');
    $('#exam_select').off('select2:unselect');
  }

  $('#exam_select').select2();
  
  $('#exam_select').on("select2:select", function (e) {
    var data = e.params.data;
    addExamToSamples(data);
    // addPatologoRow(data);
  });

  $('#exam_select').on("select2:unselect", function (e) {
    var data = e.params.data;
    removeExamFromSamples(data);
    // removePatologoRow(data.id);
  });

  $('#exam_select').on("select2:unselecting", function (e) {
    if (e.params.args.originalEvent) {
      e.params.args.originalEvent.stopPropagation();
    }
  });

  $('.switchery').remove();
  var elems = $('.switch2');
  $.each(elems, function (key, value) {
    new Switchery($(this)[0]);
  });
}

function loadExams(exams) {
  $("#exam_select").html("");
  $.each(exams, function (i, item) {
    var html = '<option data-service="'+item.service_id+'" value="'+item.id+'">'+item.name+'</option>';
    $('#exam_select').append($(html));
  });
}

function loadSamples(samples){
  $("#samples_table tbody").html("");
  var exams = [];
  $.each(samples, function(i, v){
    addSampleRow(v);
    $.each(v.sample_exams_set, function(j,item){
      exams.push(item.exam_id);
      $('.delete-'+v.id).hide();
      var html = addServiceRow(
        item.exam_name, 
        item.service_id, 
        v.id, 
        item.exam_id, 
        data_step_2.stains,
        v.identification.organs,
        v.id+"-"+($('#sampleNro-'+v.id)[0].rowSpan + 1), 
        true,
        item.is_closed
      );
      $('#sampleNro-'+v.id)[0].rowSpan = $('#sampleNro-'+v.id)[0].rowSpan + 1; 
      $('#sampleIden-'+v.id)[0].rowSpan = $('#sampleIden-'+v.id)[0].rowSpan + 1; 
      $("#sample-"+v.id).after(html);
      
      var values = [];
      $.each(item.organ_id, function(j,w){
        values.push(w.id);
      });
      $('#organs-'+v.id+"-"+$('#sampleNro-'+v.id)[0].rowSpan).val(values).trigger('change');

      if (item.sample_exam_stain_id){
        $('#stain-'+v.id+"-"+$('#sampleNro-'+v.id)[0].rowSpan).val(item.sample_exam_stain_id).trigger("change");
      } else {
        $('#stain-'+v.id+"-"+$('#sampleNro-'+v.id)[0].rowSpan).val(item.exam_stain_id).trigger("change");
      }

    });
  });

  $('.organs-select').select2();
  $('.stain-select').select2();
  $('.organs-select').on('select2:select', function(e){
    var values = e.params.data.id;
    var target_id = $(e.target).parent().parent()[0].classList[1].split("-")[2];
    var exam_id = $(e.target).parent().parent().data('sampleid');
    
    if ( $('#switchery2')[0].checked ){
      $.each($('.organs-select-'+exam_id), function(i,v){
          var old_values = $(v).val();
          old_values.push(values);
          $(v).val(old_values);
          $(v).trigger('change');
      });
    } else {
      $.each(data_step_2.samples, function(i, item2){
        if (target_id == item2.id){
          $.each($('.analis-row-'+item2.id+' .organs-select'), function(i,v){
              var old_values = $(v).val();
              old_values.push(values);
              $(v).val(old_values);
              $(v).trigger('change');
          });
        }
      });  
    }
  });

  $('.stain-select').on('select2:select', function(e){
    var values = e.params.data.id;
    var target_id = $(e.target).parent().parent()[0].classList[1].split("-")[2];
    var exam_id = $(e.target).parent().parent().data('sampleid');

    if ( $('#switchery3')[0].checked ){
      $.each($('.stain-select-'+ exam_id), function(i,v){
          $(v).val(values);
          $(v).trigger('change');
      });
    } else {
      $.each(data_step_2.samples, function(i, item2){
        if (target_id == item2.id){
          $.each($('.analis-row-'+item2.id+' .stain-select-'+ item), function(i,v){
              $(v).val(values);
              $(v).trigger('change');
          });
        }
      });  
    }
  });

  // $('.samples_exams').select2();

  // $('.samples_exams').on("select2:unselecting", function (e) {
  //   if (e.params.args.originalEvent) {
  //     e.params.args.originalEvent.stopPropagation();
  //   }
  // });
  
}

// Load prev samples and exams
function initialData(data) {
  loadSamples(data.samples);
  loadExams(data.exams);
}

function loadData(data){
  // Fill analyses
  if (data.entryform.analyses.length > 0){
    $('#pre-selected-exams-list').html("");
    $('#pre-selected-exams').show();
  }
  $.each(data.entryform.analyses, function(i, item){
    $('#pre-selected-exams-list').append("<div class='col-md-12'><b>"+$('#exam_select option[value="'+item.exam_id+'"]').text()+"</b></div>");
    //$('#exam_select option[value="'+item.exam_id+'"]').attr('disabled','disabled');
  });

  // Fill exams and organs per samples
  $.each(data.samples, function(i, item){
    $.each(item.exams_set, function(j, item2){
      var selected_exam = new Option(item2.name, item2.id, true, true);
      $('#sample-'+item.id+' .samples_exams').append(selected_exam).trigger('change');
    });

    $.each(item.organs_set, function(k, item3){
      var selected_organ = new Option(item3.name, item3.id, true, true);
      $('#sample-'+item.id+' .samples_organs').append(selected_organ).trigger('change');
    });
  });
}

function getSampleAvailableOrgans(sid){
  var organs;
  $.each(data_step_2.samples, function(index, value){
    if (sid == value.id){
      organs = value.identification.organs;
      return false;
    }
  });
  return organs;
}

function addExamToSamples(exam){
    var exam_object = data_step_2.exams.find(x => x.id == exam.id);
    $('#samples_table .samples_exams').each( function(i){
      
        if ( $('#switchery')[0].checked ){
            // add exam to all but duplicated
            var sampleId = $(this).data('index');
            $.each(data_step_2.samples, function(i, item){

                // add exam to empty samples
                if ( item.id == sampleId && !item.sample_exams_set.hasOwnProperty(exam.id) ){
                    $('.delete-'+sampleId).hide();
                    $('#sampleNro-'+sampleId)[0].rowSpan = $('#sampleNro-'+sampleId)[0].rowSpan + 1; 
                    $('#sampleIden-'+sampleId)[0].rowSpan = $('#sampleIden-'+sampleId)[0].rowSpan + 1; 
                    // show organs options
                    avail_organs = getSampleAvailableOrgans(sampleId);
                    var html = addServiceRow(
                      exam.text, 
                      $(exam.element).data('service'), 
                      sampleId, 
                      exam.id, 
                      data_step_2.stains,
                      avail_organs,
                      sampleId+"-"+($('#sampleNro-'+sampleId)[0].rowSpan),  
                      false
                    );
                    $("#sample-"+sampleId).after(html);

                    if (exam_object.stain_id){
                      $('#stain-'+sampleId+"-"+$('#sampleNro-'+sampleId)[0].rowSpan ).val(exam_object.stain_id).trigger("change");
                    }
                    return false;
                }
            });
        } else {
            var sampleId = $(this).data('index');
            $.each(data_step_2.samples, function(i, item){
                // add exam to empty samples
                if (item.id == sampleId && _.isEmpty(item.sample_exams_set)){
                    $('.delete-'+sampleId).hide();
                    $('#sampleNro-'+sampleId)[0].rowSpan = $('#sampleNro-'+sampleId)[0].rowSpan + 1; 
                    $('#sampleIden-'+sampleId)[0].rowSpan = $('#sampleIden-'+sampleId)[0].rowSpan + 1; 
                    // show organs options
                    avail_organs = getSampleAvailableOrgans(sampleId);
                    var html = addServiceRow(
                      exam.text, 
                      $(exam.element).data('service'), 
                      sampleId, 
                      exam.id,
                      data_step_2.stains, 
                      avail_organs,
                      sampleId+"-"+($('#sampleNro-'+sampleId)[0].rowSpan), 
                      false
                    ); 
                    $("#sample-"+sampleId).after(html);

                    if (exam_object.stain_id){
                      $('#stain-'+sampleId+"-"+$('#sampleNro-'+sampleId)[0].rowSpan).val(exam_object.stain_id).trigger("change");
                    }
                    return false;
                }
            });
        }


    });

    $('.organs-select-'+ exam.id).select2();
    $('.stain-select-'+ exam.id).select2();
    
    $('.organs-select-'+ exam.id).on('select2:select', function(e){
      var values = e.params.data.id;
      var target_id = $(e.target).parent().parent()[0].classList[1].split("-")[2];
      
      if ( $('#switchery2')[0].checked ){
        $.each($('.organs-select-'+ exam.id), function(i,v){
            var old_values = $(v).val();
            old_values.push(values);
            $(v).val(old_values);
            $(v).trigger('change');
        });
      } else {
        $.each(data_step_2.samples, function(i, item2){
          if (target_id == item2.id){
            $.each($('.analis-row-'+item2.id+' .organs-select-'+ exam.id), function(i,v){
                var old_values = $(v).val();
                old_values.push(values);
                $(v).val(old_values);
                $(v).trigger('change');
            });
          }
        });  
      }
    });

    $('.stain-select-'+ exam.id).on('select2:select', function(e){
      var values = e.params.data.id;
      var target_id = $(e.target).parent().parent()[0].classList[1].split("-")[2];
      
      if ( $('#switchery3')[0].checked ){
        $.each($('.stain-select-'+ exam.id), function(i,v){
            $(v).val(values);
            $(v).trigger('change');
        });
      } else {
        $.each(data_step_2.samples, function(i, item2){
          if (target_id == item2.id){
            $.each($('.analis-row-'+item2.id+' .stain-select-'+ exam.id), function(i,v){
                $(v).val(values);
                $(v).trigger('change');
            });
          }
        });  
      }
    });
}

function removeExamFromSamples(exam){

  $('#samples_table .analis-row').each( function(i){
    if($(this).data('sampleid') == exam.id){
      if ( !$(this).data('prevdata') ) {
        var sampleIndex = $(this).data('sampleindex');
        $('#sampleNro-'+sampleIndex)[0].rowSpan = $('#sampleNro-'+sampleIndex)[0].rowSpan - 1; 
        $('#sampleIden-'+sampleIndex)[0].rowSpan = $('#sampleIden-'+sampleIndex)[0].rowSpan - 1; 
        $(this).remove();
        if ( $('#sampleIden-'+sampleIndex)[0].rowSpan == 1 ) {
          $('.delete-'+sampleIndex).show();
        }
      }
    }
  }); 
}

function initialConf() {
  $('#exam_select').select2();
}

function validate_step_2(){
  // Validates sample exam assignation
  var missing_exams_select = false;
  $('#samples_table .samples_exams').each( function(i){
    var id = $(this).data('index');
    if ( $('.analis-row-'+id).length <= 0 ){
      $(this).focus();
      missing_exams_select = true;
      return 0;
    }
  });

  if (missing_exams_select){
    toastr.error(
      'Para continuar debes asignar al menos un análisis a realizar por muestra.', 
      'Ups!', 
      {positionClass: 'toast-top-full-width', containerId: 'toast-bottom-full-width'}
    );
    return 0;
  }

  // Validates sample organ assignation
  var missing_organs_select = false;
  $('#samples_table .organs-select').each( function(i){
    if ( $(this).find(":selected").length <= 0 ){
      $(this).focus();
      missing_organs_select = true;
      return 0;
    }
  });

  if (missing_organs_select){
    toastr.error(
      'Para continuar es necesario definir el o los organos por muestra.', 
      'Ups!', 
      {positionClass: 'toast-top-full-width', containerId: 'toast-bottom-full-width'}
    );
    return 0;
  }

  // Validates exam selection
  // if ( $('#exam_select :selected').length <= 0 ) {
  //   toastr.error(
  //     'Para continuar debes tener seleccionado al menos un análisis.', 
  //     'Ups!', 
  //     {positionClass: 'toast-top-full-width', containerId: 'toast-bottom-full-width'}
  //   );
  //   $('#exam_select').focus();
  //   return 0;
  // }

  return 1;
}


function addAnalysisTemplate(data) {
  var analysisTemplate = document.getElementById("analysis_template").innerHTML;

  var templateFn = _.template(analysisTemplate);
  var templateHTML = templateFn(data);

  $("#exam_group").html(templateHTML)
  $('.samples_organs').select2();
  $('.samples_analysis').select2();

  $('.samples_organs').on("select2:unselecting", function (e) {
    if (e.params.args.originalEvent) {
      e.params.args.originalEvent.stopPropagation();
    }
  });

  $('.samples_analysis').on("select2:unselecting", function (e) {
    if (e.params.args.originalEvent) {
      e.params.args.originalEvent.stopPropagation();
    }
  });
  
}

function addSampleRow(sample) {
  var sampleRowTemplate = document.getElementById("sample_row").innerHTML;

  var templateFn = _.template(sampleRowTemplate);
  var templateHTML = templateFn({'sample': sample, 'organs': organs});

  $("#samples_table tbody").append(templateHTML)
}

function addServiceRow(analisis, analisis_type, sampleId, sampleIndex, stains, organs, optionId = null, prevData = false, is_closed = false) {
  var sampleRowTemplate = document.getElementById("add_analisis").innerHTML;

  var templateFn = _.template(sampleRowTemplate);
  var templateHTML = templateFn({'organs': organs, 'stains':stains, 'type': analisis_type, 'analisis': analisis, 'sampleId': sampleId, 'sampleIndex': sampleIndex, 'optionId': optionId, 'prevData': prevData, 'is_closed': is_closed});
  return templateHTML;
}

function deleteAnalisis(sampleId, sampleIndex, active, prevData){
  if(active)
  {
    if (prevData){
      swal({
        title: "Confirmación",
        text: "El servicio que desea eliminar de la muestra ha sido asignado previamente y es posible que ya se encuentre en proceso, por lo que podría estar perdiendo trabajo realizado. ¿Confirma que desea eliminar?",
        icon: "warning",
        showCancelButton: true,
        buttons: {
          cancel: {
              text: "Cancelar",
              value: null,
              visible: true,
              className: "btn-warning",
              closeModal: true,
          },
          confirm: {
              text: "Continuar",
              value: true,
              visible: true,
              className: "",
              closeModal: true,
          }
        }
      }).then(isConfirm => {
        if (isConfirm) {
          $('#analisis-'+sampleId+'-'+sampleIndex).remove();
          $('#sampleNro-'+sampleId)[0].rowSpan = $('#sampleNro-'+sampleId)[0].rowSpan - 1; 
          $('#sampleIden-'+sampleId)[0].rowSpan = $('#sampleIden-'+sampleId)[0].rowSpan - 1; 
          if($('#sampleIden-'+sampleId)[0].rowSpan == 1)
            $('.delete-'+sampleId).show();
          var exist = 0;
          $('#samples_table .analis-row').each( function(i){
            if($(this).data('sampleid') == sampleIndex){
              exist +=1;
            }
          }); 
          if(!exist){
            var old_values = $('#exam_select').val();
            old_values.splice(old_values.indexOf(sampleIndex), 1);
            $('#exam_select').val(old_values);
            $('#exam_select').trigger('change');
            $('#exam-'+sampleIndex).remove();
          }
        }
      });
    } else {
      $('#analisis-'+sampleId+'-'+sampleIndex).remove();
      $('#sampleNro-'+sampleId)[0].rowSpan = $('#sampleNro-'+sampleId)[0].rowSpan - 1; 
      $('#sampleIden-'+sampleId)[0].rowSpan = $('#sampleIden-'+sampleId)[0].rowSpan - 1; 
      if($('#sampleIden-'+sampleId)[0].rowSpan == 1)
        $('.delete-'+sampleId).show();
      var exist = 0;
      $('#samples_table .analis-row').each( function(i){
        if($(this).data('sampleid') == sampleIndex){
          exist +=1;
        }
      }); 
      if(!exist){
        var old_values = $('#exam_select').val();
        old_values.splice(old_values.indexOf(sampleIndex), 1);
        $('#exam_select').val(old_values);
        $('#exam_select').trigger('change');
        $('#exam-'+sampleIndex).remove();
      }
    }
    
  }
}

// function addPatologoRow(exam) {
//   var sampleRowTemplate = document.getElementById("patologo_row").innerHTML;

//   var templateFn = _.template(sampleRowTemplate);
//   var templateHTML = templateFn({'exam': exam, 'patologos': patologos_list});

//   $("#patologo_table tbody").append(templateHTML)
//   $('#patologos-select-'+exam.id).select2();
// }

// function removePatologoRow(exam_id){
//   $('#exam-'+exam_id).remove();
// }