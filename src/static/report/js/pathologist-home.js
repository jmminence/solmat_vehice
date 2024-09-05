$(document).ready(function () {
  const year = $("#year");
  const month = $("#month");
  const pathologist = $("#pathologist");

  const pendingNumber = $("#pendingNumber");
  const pendingTable = $("#pendingTable");

  const currentNumber = $("#currentNumber");
  const currentTable = $("#currentTable");

  const unreviewNumber = $("#unreviewNumber");
  const unreviewTable = $("#unreviewTable");

  const efficiencyTable = $("#efficiencyTable");

  let averageEfficiency = echarts.init(
    document.getElementById("averageEfficiency")
  );

  let avgEffOptions = {
    tooltip: {
      formatter: "{a} <br/>{b} : {c}%",
    },
    series: [
      {
        type: "gauge",
        detail: { formatter: "{value}" },
        startAngle: 180,
        endAngle: 0,
        min: 0,
        max: 7,
        splitNumber: 1,
        data: [{ value: 0, name: "Promedio Mensual" }],
        axisLine: {
          lineStyle: {
            color: [
              [0.57, "#FF6E76"],
              [0.7, "#58D9F9"],
              [1, "#7CFFB2"],
            ],
          },
        },
        splitLine: {
          show: false,
        },
        axisTick: {
          show: false,
        },
        axisLabel: {
          show: false,
        },
        title: {
          show: false,
        },
        detail: {
          formatter: (value) => value.toFixed(1),
        },
        tooltip: {
          formatter: "{b}: {c}",
        },
      },
    ],
  };

  averageEfficiency.setOption(avgEffOptions);

  let monthlyEfficiency = echarts.init(
    document.getElementById("monthlyEfficiency")
  );

  let monthlyEffOptions = {
    xAxis: {
      type: "category",
      data: [],
    },
    yAxis: {
      type: "value",
    },
    series: [
      {
        data: [],
        type: "line",
        label: {
          show: true,
          formatter: (value) => value.value.toFixed(1),
        },
      },
    ],
  };

  let barOptions = {
    xAxis: {
      type: "category",
      data: [],
    },
    yAxis: {
      type: "value",
    },
    series: [
      {
        data: [],
        type: "bar",
        label: {
          show: true,
          formatter: (value) => value.value.toFixed(1),
        },
      },
    ],
  };

  monthlyEfficiency.setOption(monthlyEffOptions);

  let data;

  getData();

  /* FUNCTIONS */
  function dateDiff(a, b = null) {
    const date = new Date(a);
    const currentDate = b == null ? new Date() : new Date(b);
    const diffTime = currentDate - date;

    if (diffTime < 0) {
      return 0;
    }

    return Math.ceil(Math.abs(diffTime) / (1000 * 60 * 60 * 24));
  }

  function filterPending() {
    return data.filter((analysis) => {
      const is_closed = analysis.workflow.fields.form_closed;
      const is_cancelled = analysis.workflow.fields.form_cancelled;
      const pre_report_started = analysis.report.fields.pre_report_started;
      const is_assigned = analysis.report.fields.patologo != null;

      return !(is_closed || is_cancelled) && is_assigned && !pre_report_started;
    });
  }

  function filterCurrent() {
    return data.filter((analysis) => {
      const is_closed = analysis.workflow.fields.form_closed;
      const is_cancelled = analysis.workflow.fields.form_cancelled;
      const pre_report_started = analysis.report.fields.pre_report_started;
      const pre_report_ended = analysis.report.fields.pre_report_ended;
      const is_assigned = analysis.report.fields.patologo != null;

      return (
        !(is_closed || is_cancelled) &&
        is_assigned &&
        pre_report_started &&
        !pre_report_ended
      );
    });
  }

  function filterUnreview() {
    return data.filter((analysis) => {
      const is_closed = analysis.workflow.fields.form_closed;
      const is_cancelled = analysis.workflow.fields.form_cancelled;
      const pre_report_started = analysis.report.fields.pre_report_started;
      const pre_report_ended = analysis.report.fields.pre_report_ended;
      const is_assigned = analysis.report.fields.patologo != null;

      return (
        !(is_closed || is_cancelled) &&
        is_assigned &&
        pre_report_started &&
        pre_report_ended
      );
    });
  }

  function filterDone() {
    return data.filter((analysis) => {
      const is_closed = analysis.workflow.fields.form_closed;
      const is_assigned = analysis.report.fields.patologo != null;

      return is_closed && is_assigned;
    });
  }

  function groupByMonth(data, key) {
    return data.reduce(function (rv, x) {
      (rv["workflow"][x[key]] = rv[x[key]] || []).push(x);
      return rv;
    }, {});
  }

  function updateView() {
    if ($.fn.DataTable.isDataTable("#pendingTable")) {
      pendingTable.DataTable().clear().destroy();
    }

    const pending = filterPending();
    pendingNumber.text(pending.length);
    pendingTable.DataTable({
      data: pending,

      columns: [
        {
          data: "case.fields.no_caso",
          name: "case",
          type: "string",
          title: "Caso",
        },
        {
          data: "exam.fields.name",
          name: "exam",
          type: "string",
          title: "Servicio",
        },
        {
          data: "stain.fields.abbreviation",
          name: "stain",
          type: "num",
          title: "Tincion",
        },
        {
          data: "user.fields",
          name: "pathologist",
          type: "string",
          title: "Patologo",
          render: (data) => {
            return `${data.first_name[0]}${data.last_name[0]}`;
          },
        },
        {
          data: "case.fields.created_at",
          name: "entry_date",
          type: "string",
          title: "Ingreso",
          render: (data) => {
            const date = new Date(data);
            return date.toLocaleDateString();
          },
        },
        {
          data: "report.fields.assignment_done_at",
          name: "derived_at",
          type: "num",
          title: "Derivacion",
          render: (data) => {
            const date = new Date(data);
            return date.toLocaleDateString();
          },
        },
        {
          data: "report.fields.assignment_deadline",
          name: "derived_at",
          type: "num",
          title: "Plazo",
          render: (data) => {
            const date = new Date(data);
            return date.toLocaleDateString();
          },
        },
        {
          data: "report.fields.assignment_deadline",
          name: "delay",
          type: "num",
          title: "Atraso",
          render: (data) => {
            return dateDiff(data);
          },
        },
      ],

      oLanguage: {
        sUrl: "https://cdn.datatables.net/plug-ins/1.10.16/i18n/Spanish.json",
      },
    });

    if ($.fn.DataTable.isDataTable("#currentTable")) {
      currentTable.DataTable().clear().destroy();
    }

    const current = filterCurrent();
    currentNumber.text(current.length);
    currentTable.DataTable({
      data: current,

      columns: [
        {
          data: "case.fields.no_caso",
          name: "case",
          type: "string",
          title: "Caso",
        },
        {
          data: "exam.fields.name",
          name: "exam",
          type: "string",
          title: "Servicio",
        },
        {
          data: "stain.fields.abbreviation",
          name: "stain",
          type: "num",
          title: "Tincion",
        },
        {
          data: "user.fields",
          name: "pathologist",
          type: "string",
          title: "Patologo",
          render: (data) => {
            return `${data.first_name[0]}${data.last_name[0]}`;
          },
        },
        {
          data: "case.fields.created_at",
          name: "entry_date",
          type: "string",
          title: "Ingreso",
          render: (data) => {
            const date = new Date(data);
            return date.toLocaleDateString();
          },
        },
        {
          data: "report.fields.assignment_done_at",
          name: "derived_at",
          type: "num",
          title: "Derivacion",
          render: (data) => {
            const date = new Date(data);
            return date.toLocaleDateString();
          },
        },
        {
          data: "report.fields.assignment_deadline",
          name: "derived_at",
          type: "num",
          title: "Plazo",
          render: (data) => {
            const date = new Date(data);
            return date.toLocaleDateString();
          },
        },
        {
          data: "report.fields.pre_report_started_at",
          name: "delay",
          type: "num",
          title: "Inicio lectura",
          render: (data) => {
            const date = new Date(data);
            return date.toLocaleDateString();
          },
        },
        {
          data: "report.fields.assignment_deadline",
          name: "delay",
          type: "num",
          title: "Atraso",
          render: (data) => {
            return dateDiff(data);
          },
        },
        {
          data: "report.fields.pre_report_started_at",
          name: "delay",
          type: "num",
          title: "En Lectura",
          render: (data) => {
            return dateDiff(data);
          },
        },
      ],

      oLanguage: {
        sUrl: "https://cdn.datatables.net/plug-ins/1.10.16/i18n/Spanish.json",
      },
    });

    if ($.fn.DataTable.isDataTable("#unreviewTable")) {
      unreviewTable.DataTable().clear().destroy();
    }

    const unreview = filterUnreview();
    unreviewNumber.text(unreview.length);
    unreviewTable.DataTable({
      data: unreview,

      columns: [
        {
          data: "case.fields.no_caso",
          name: "case",
          type: "string",
          title: "Caso",
        },
        {
          data: "exam.fields.name",
          name: "exam",
          type: "string",
          title: "Servicio",
        },
        {
          data: "stain.fields.abbreviation",
          name: "stain",
          type: "num",
          title: "Tincion",
        },
        {
          data: "user.fields",
          name: "pathologist",
          type: "string",
          title: "Patologo",
          render: (data) => {
            return `${data.first_name[0]}${data.last_name[0]}`;
          },
        },
        {
          data: "case.fields.created_at",
          name: "entry_date",
          type: "string",
          title: "Ingreso",
          render: (data) => {
            const date = new Date(data);
            return date.toLocaleDateString();
          },
        },
        {
          data: "report.fields.pre_report_started_at",
          name: "delay",
          type: "num",
          title: "Inicio lectura",
          render: (data) => {
            const date = new Date(data);
            return date.toLocaleDateString();
          },
        },
        {
          data: "report.fields.pre_report_ended_at",
          name: "derived_at",
          type: "num",
          title: "Fin lectura",
          render: (data) => {
            const date = new Date(data);
            return date.toLocaleDateString();
          },
        },
        {
          data: "report.fields",
          name: "derived_at",
          type: "num",
          title: "Dias en lectura",
          render: (data) => {
            return dateDiff(
              data.pre_report_started_at,
              data.pre_report_ended_at
            );
          },
        },
        {
          data: "report.fields.pre_report_ended_at",
          name: "delay",
          type: "num",
          title: "En Revision",
          render: (data) => {
            return dateDiff(data);
          },
        },
      ],

      oLanguage: {
        sUrl: "https://cdn.datatables.net/plug-ins/1.10.16/i18n/Spanish.json",
      },
    });

    if ($.fn.DataTable.isDataTable("#efficiencyTable")) {
      efficiencyTable.DataTable().clear().destroy();
    }

    const efficiency = filterDone();
    efficiencyTable.DataTable({
      data: efficiency,

      columns: [
        {
          data: "case.fields.no_caso",
          name: "case",
          type: "string",
          title: "Caso",
        },
        {
          data: "report.fields.report_code",
          name: "reportCode",
          type: "string",
          title: "Informe",
        },
        {
          data: "exam.fields.name",
          name: "service",
          type: "string",
          title: "Servicio",
        },
        {
          data: "case.fields.created_at",
          name: "createdAt",
          type: "string",
          title: "Ingreso",
          render: (data) => {
            const date = new Date(data);
            return date.toLocaleDateString();
          },
        },
        {
          data: "workflow.fields.closed_at",
          name: "closedAt",
          type: "num",
          title: "Emisión",
          render: (data) => {
            const date = new Date(data);
            return date.toLocaleDateString();
          },
        },
        {
          data: "user.fields",
          name: "user",
          type: "num",
          title: "Patólogo",
          render: (data) => {
            return `${data.first_name[0]}${data.last_name[0]}`;
          },
        },
        {
          data: "report.fields.score_diagnostic",
          name: "score",
          type: "num",
          title: "Calificación",
        },
      ],

      oLanguage: {
        sUrl: "https://cdn.datatables.net/plug-ins/1.10.16/i18n/Spanish.json",
      },
    });

    let sumEffValue = 0;

    for (const row of efficiency) {
      sumEffValue += row.report.fields.score_diagnostic;
    }

    const length = efficiency.filter(
      (row) => row.report.fields.score_diagnostic > 0
    ).length;

    const avg = sumEffValue / length;

    avgEffOptions.series[0].data[0].value = avg;
    averageEfficiency.setOption(avgEffOptions, true);

    const monthlyGrouped = _.groupBy(efficiency, (row) => {
      const date = new Date(row.workflow.fields.closed_at);
      return `${date.getFullYear()}/${date.getMonth() + 1}`;
    });

    xAxis = [];
    yAxis = [];

    for (const month in monthlyGrouped) {
      const group = monthlyGrouped[month];

      const length = group.filter(
        (row) => row.report.fields.score_diagnostic > 0
      ).length;

      let sumEffValue = 0;

      for (const row of group) {
        sumEffValue += row.report.fields.score_diagnostic;
      }

      xAxis.push(month);
      yAxis.push(sumEffValue / length);
    }

    monthlyEffOptions.xAxis.data = xAxis;
    monthlyEffOptions.series[0].data = yAxis;

    monthlyEfficiency.setOption(monthlyEffOptions, true);
  }

  function getData() {
    const date_start = $("#dateStart").val();
    const date_end = $("#dateEnd").val();
    const user_id = $("#pathologist").val();
    Swal.fire({
      title: "Cargando...",
      allowOutsideClick: false,
    });
    Swal.showLoading();

    $.ajax(Urls["report:pathologist"](), {
      data: JSON.stringify({ date_start, date_end, user_id }),

      method: "POST",

      headers: {
        "X-CSRFToken": getCookie("csrftoken"),
      },

      contentType: "application/json; charset=utf-8",

      success: (_data, textStatus) => {
        Swal.close();
        // REFACTOR THIS IF DJANGO REST FRAMEWORK IS USED
        data = JSON.parse(_data).map((row) => {
          return {
            report: JSON.parse(row.report)[0],
            exam: JSON.parse(row.exam)[0],
            case: JSON.parse(row.case)[0],
            user: JSON.parse(row.user)[0],
            stain: JSON.parse(row.stain)[0],
            workflow: JSON.parse(row.workflow)[0],
          };
        });
        updateView();
      },
      error: (xhr, textStatus, error) => {
        Swal.fire({
          icon: "error",
        });
      },
    });
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

  /* EVENTS */

  $("#btnFilter").click(() => {
    getData();
  });
});
