var patologos_list;
function init_step_4(active = true) {
  var entryform_id = $('#entryform_id').val();
  var url = Urls.cassette_entryform_id(entryform_id);

  $.ajax({
    type: "GET",
    url: url,
    async: false,
  })
    .done(function (data) {
      $('.showShareBtn').removeClass("hidden");
      $('.showLogBtn').removeClass("hidden");
      $('.showSummaryBtn').removeClass("hidden");
      $('.showAttachedFilesBtn').removeClass("hidden");
      if(active){
        $('.newAnalysisBtn').removeClass("hidden");
      }
      $('.newAnalysisBtn5').addClass("hidden");
      // fillSummary(data);
      patologos_list = data.patologos;
      fillNewAnalysis(data);
      loadBlockTable(data, active); 
    })
    .fail(function () {
      console.log("Fail")
    })
    
    if ($('#exam_new_select').hasClass("select2-hidden-accessible")) {
      $('#exam_new_select').select2('destroy');
      $('#exam_new_select').off('select2:select');
      $('#exam_new_select').off('select2:unselect');
    }
  
    $('#exam_new_select').select2();
    
    $('#exam_new_select').on("select2:select", function (e) {
      var data = e.params.data;
      addNewExamToSamples(data);
      addPatologoRow_4(data);
    });
  
    $('#exam_new_select').on("select2:unselect", function (e) {
      var data = e.params.data;
      removeNewExamFromSamples(data);
      removePatologoRow_4(data.id);
    });
  
    $('#exam_new_select').on("select2:unselecting", function (e) {
      if (e.params.args.originalEvent) {
        e.params.args.originalEvent.stopPropagation();
      }
    });
}

$(document).on('change', '#block_table :checkbox', function (e) {
  if (e.target.checked) {
    $("[name='" + e.target.id + "']").val(moment().format("DD/MM/YYYY HH:mm:ss"));
  } else {
    $("[name='" + e.target.id + "']").val("");
  }
})

$(document).on('click', '.block_start_all', function (e) {
  lockScreen(1);
  $("input[type=checkbox][id^='block_start_block']" ).trigger('click');
  lockScreen(0);
});

$(document).on('click', '.block_end_all', function (e) {
  lockScreen(1);
  $("input[type=checkbox][id^='block_end_block']" ).trigger('click');
  lockScreen(0);
});

$(document).on('click', '.slice_start_all', function (e) {
  lockScreen(1);
  $("input[type=checkbox][id^='block_start_slice']" ).trigger('click');
  lockScreen(0);
});

$(document).on('click', '.slice_end_all', function (e) {
  lockScreen(1);
  $("input[type=checkbox][id^='block_end_slice']" ).trigger('click');
  lockScreen(0);
});

$(document).on('click', '#saveTimingStep4', function (e) {
  lockScreen(1);
  var form_data = $('#block_table_wrapper :input').serialize();
  var url = Urls.save_block_timing();
  $.ajax({
    type: "POST",
    url: url,
    data: form_data,
    async: false,
  })
  .done(function (data) {
    lockScreen(0);
    if (data.ok) {
      toastr.success('', 'Guardado.');
    } else {
      toastr.error('', 'No ha sido posible guardar. Contacte un administrador.');
    }    
    response = data;
  })
  .fail(function (data) {
    lockScreen(0);
    toastr.error('', 'No ha sido posible guardar. Contacte un administrador.');
  })
});

function loadBlockTable(data, active = true) {
  if ($.fn.DataTable.isDataTable('#block_table')) {
    $('#block_table').DataTable().clear().destroy();
  }

  populateBlockTable(data, active);

  var elems = Array.prototype.slice.call(document.querySelectorAll('.switchery'));

  elems.forEach(function (html) {
    new Switchery(html);
  });

  $('[data-toggle="popover"]').popover();

  $('#block_table').DataTable({
    ordering: false,
    paginate: false,
    bFilter: false,
    // scrollX: true,
    language: {
      url: "https://cdn.datatables.net/plug-ins/1.10.16/i18n/Spanish.json"
    },
  });
}

function populateBlockTable(data, active = true) {
  console.log(data)
  $.each(data.cassettes, function (i, item) {
    var row = {};

    // row.sample_id = item.sample.id;
    // row.sample_index = item.sample.index;
    row.cassette_name = item.cassette_name;
    row.cassette_pk = item.id;
    row.cassette_index = item.index;
    row.organs = item.organs_set.join(", ");

    var samples_index_comm_sep = '';
    $.each(item.samples_set, function(j, sample){
      if (j == 0){
        samples_index_comm_sep += sample.index;
      } else {
        samples_index_comm_sep += ', '+sample.index;
      }
    });
    row.samples = samples_index_comm_sep;
    row.no_slice = item.slices_set.length;

    if (item.slices_set.length > 0) {
      row.start_block = item.slices_set[0].start_block;
      row.end_block = item.slices_set[0].end_block;
      row.start_slice = item.slices_set[0].start_slice;
      row.end_slice = item.slices_set[0].end_slice;
    } else {
      row.start_block = "";
      row.end_block = "";
      row.start_slice = "";
      row.end_slice = "";
    }

    row.slice_info = "<ol>";
    $.each(item.slices_set, function (k, v) {
      row.slice_info += "<li><p><strong>Cassette:</strong> " + row.cassette_name + " <strong> </br>Muestras: </strong>\
      " + row.samples + " <strong> </br>Corte: </strong>" +v.slice_name+" <strong>\
      </br>An&aacute;lisis: </strong>" + v.exam + "</p></li>"
    });
    row.slice_info += "</ol>";

    addBlockRow(row)

    if (row.start_block) {
      $("#block_start_block_" + i).trigger("click");
    }
    if(!active)
      $("#block_start_block_" + i).attr("disabled", true);
    if (row.end_block) {
      $("#block_end_block_" + i).trigger("click");
    }
    if(!active)
      $("#block_end_block_" + i).attr("disabled", true);
    if (row.start_slice) {
      $("#block_start_slice_" + i).trigger("click");
    }
    if(!active)
      $("#block_start_slice_" + i).attr("disabled", true);
    if (row.end_slice) {
      $("#block_end_slice_" + i).trigger("click");
    }
    if(!active)
      $("#block_end_slice_" + i).attr("disabled", true);
  });
}

function addBlockRow(data) {
  var blockRowTemplate = document.getElementById("block_dyeing_row").innerHTML;

  var templateFn = _.template(blockRowTemplate);
  var templateHTML = templateFn(data);

  $("#block_table tbody").append(templateHTML)
}

function fillNewAnalysis(data) {
  organs_list = data.organs;
  loadNewSamples(data.samples, data.organs);
  loadNewExams4(data.exams_set);
  $('#patologo_table_4 tbody').html('');
  $.each(data.entryform.analyses, function(i, item){
    $('#exam_new_select option[value="'+item.exam_id+'"]').prop('selected', true);
    addPatologoRow_4({text: item.exam__name, id: item.exam_id});
    $('#patologos-select_4-'+item.exam_id).val(item.patologo_id);
    $('#patologos-select_4-'+item.exam_id).trigger('change');
    $('#patologos-select_4-'+item.exam_id).attr('disabled', 'disabled');
  });
  $('#exam_new_select').trigger('change');
}

function loadNewExams4(exams) {
  $("#exam_new_select").html("");
  $.each(exams, function (i, item) {
    var html = '<option data-examtype="'+item.exam_type+'" value="'+item.id+'">'+item.name+'</option>';
    $('#exam_new_select').append($(html));
  });
}

function addNewExamToSamples(exam){
  $('#samples_new_table .samples_new_exams').each( function(i){
      var sampleId = $(this).data('index');
      $('.delete_new-'+sampleId).hide();
      $('#sampleNro_new-'+sampleId)[0].rowSpan = $('#sampleNro_new-'+sampleId)[0].rowSpan + 1; 
      $('#sampleIden_new-'+sampleId)[0].rowSpan = $('#sampleIden_new-'+sampleId)[0].rowSpan + 1; 
      //show organs options
      var html = addNewOrgansOptions(exam.text, $(exam.element).data('examtype'), sampleId, exam.id);
      $("#sample_new-"+sampleId).after(html);
    // }
  }); 
  $('.organs_new_select-'+ exam.id).select2();
  $('.organs_new_select-'+ exam.id).on('select2:select', function(e){
    var values = e.params.data.id;
    $.each($('.organs_new_select-'+ exam.id), function(i,v){
      var old_values = $(v).val();
      old_values.push(values);
      $(v).val(old_values);
      $(v).trigger('change');
    });
  });
}

function removeNewExamFromSamples(exam){
  $('#samples_new_table .analis_new_row').each( function(i){
    if($(this).data('sampleid') == exam.id && !$(this).hasClass('old_row')){
      var sampleIndex = $(this).data('sampleindex');
      $('#sampleNro_new-'+sampleIndex)[0].rowSpan = $('#sampleNro_new-'+sampleIndex)[0].rowSpan - 1; 
      $('#sampleIden_new-'+sampleIndex)[0].rowSpan = $('#sampleIden_new-'+sampleIndex)[0].rowSpan - 1; 
      $(this).remove();
      if($('#sampleIden_new-'+sampleIndex)[0].rowSpan == 1)
        $('.delete_new-'+sampleIndex).show();
    }
  }); 
}

function loadNewSamples(samples, organs){
  $("#samples_new_table tbody").html("");
  $.each(samples, function (i, v){
    addNewSampleRow(v, organs);
    $.each(v.sample_exams_set, function(j,item){
      $('.delete_new-'+v.id).hide();
      var html = addOldOrgansOptions(item.exam_name, item.exam_type, v.id, item.exam_id, v.id+"-"+($('#sampleNro_new-'+v.id)[0].rowSpan + 1));
      $('#sampleNro_new-'+v.id)[0].rowSpan = $('#sampleNro_new-'+v.id)[0].rowSpan + 1; 
      $('#sampleIden_new-'+v.id)[0].rowSpan = $('#sampleIden_new-'+v.id)[0].rowSpan + 1;
      $("#sample_new-"+v.id).after(html);
     
      $('.organs_new_select-'+ item.exam_id).select2();
      $('.organs_new_select-'+ item.exam_id).on('select2:select', function(e){
        var values = e.params.data.id;
        $.each($('.organs_new_select-'+ item.exam_id), function(i,v){
          var old_values = $(v).val();
          old_values.push(values);
          $(v).val(old_values);
          $(v).trigger('change');
        });
      });
      var values = [];
      $.each(item.organ_id, function(j,w){
        values.push(w.id);
      });
      $('#select'+v.id+"-"+$('#sampleNro_new-'+v.id)[0].rowSpan).val(values);
      $('#select'+v.id+"-"+$('#sampleNro_new-'+v.id)[0].rowSpan).trigger('change');
    });
  });
 

  $('.samples_organs').select2();
}

function addNewSampleRow (sample, organs) {
  var sampleRowTemplate = document.getElementById("sample_new_row").innerHTML;

  var templateFn = _.template(sampleRowTemplate);
  var templateHTML = templateFn({'sample': sample, 'organs': organs});

  $("#samples_new_table tbody").append(templateHTML)
}

function addNewOrgansOptions(analisis, analisis_type, sampleId, sampleIndex, optionId = null) {
  var sampleRowTemplate = document.getElementById("add_new_analisis").innerHTML;

  var templateFn = _.template(sampleRowTemplate);
  var templateHTML = templateFn({'organs': organs_list, 'type': analisis_type, 'analisis': analisis, 'sampleId': sampleId, 'sampleIndex': sampleIndex, 'optionId': optionId});
  return templateHTML;
}

function addOldOrgansOptions(analisis, analisis_type, sampleId, sampleIndex, optionId = null) {
  var sampleRowTemplate = document.getElementById("add_old_analisis").innerHTML;

  var templateFn = _.template(sampleRowTemplate);
  var templateHTML = templateFn({'organs': organs_list, 'type': analisis_type, 'analisis': analisis, 'sampleId': sampleId, 'sampleIndex': sampleIndex, 'optionId': optionId});
  return templateHTML;
}

function deleteNewAnalisis(sampleId, sampleIndex){
  $('#analisis_new-'+sampleId+'-'+sampleIndex).remove();
  $('#sampleNro_new-'+sampleId)[0].rowSpan = $('#sampleNro_new-'+sampleId)[0].rowSpan - 1; 
  $('#sampleIden_new-'+sampleId)[0].rowSpan = $('#sampleIden_new-'+sampleId)[0].rowSpan - 1; 
  if($('#sampleIden_new-'+sampleId)[0].rowSpan == 1)
    $('.delete_new-'+sampleId).show();
  var exist = 0;
  $('#samples_new_table .analis_new_row').each( function(i){
    if($(this).data('sampleid') == sampleIndex){
      exist +=1;
    }
  }); 
  if(!exist){
    var old_values = $('#exam_new_select').val();
    old_values.splice(old_values.indexOf(sampleIndex), 1);
    $('#exam_new_select').val(old_values);
    $('#exam_new_select').trigger('change');
  }
}

function submitNewAnalysis(){
  var url = Urls.workflow();
  
  var disform = $("#modal_3").find(':disabled').prop('disabled', false);
  var form_data = $("#modal_3").find("select, input").serialize();
  disform.prop('disabled', true);

  var response;
  $.ajax({
    type: "POST",
    url: url,
    data: form_data + "&id_next_step=3&previous_step=0",
    async: false,
  })
  .done(function (data) {
    init_step_4();
    $("#new_analysis").modal("hide");

  })
  .fail(function (data) {
    console.log("Fail");
  })
}

function addPatologoRow_4(exam) {
  var sampleRowTemplate = document.getElementById("patologo_row_4").innerHTML;

  var templateFn = _.template(sampleRowTemplate);
  var templateHTML = templateFn({'exam': exam, 'patologos': patologos_list});

  $("#patologo_table_4 tbody").append(templateHTML)
  $('#patologos-select_4-'+exam.id).select2();
}

function removePatologoRow_4(exam_id){
  $('#exam_4-'+exam_id).remove();
}