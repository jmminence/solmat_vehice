// RESPONSE TIME CHARTS
let weeklyDaysResponseChart = echarts.init(
  document.getElementById("weeklyDaysResponse")
);
let weeklyAnalysisChart = echarts.init(
  document.getElementById("weeklyAnalysis")
);
let totalsResponseTimeChart = echarts.init(
  document.getElementById("totalsResponseTime")
);

let weeklyDaysResponseOption = {
  title: {
    text: "Semanas vs Dias por etapas",
    padding: [20, 0],
  },
  tooltip: {
    trigger: "axis",
  },
  xAxis: {
    type: "category",
    boundaryGap: false,
    data: [],
    name: "Semanas",
    nameLocation: "center",
    nameGap: 50,
  },
  yAxis: [
    {
      type: "value",
      name: "Dias",
      nameRotate: 90,
      nameGap: 50,
      nameLocation: "center",
    },
  ],
  series: [],
};

let weeklyAnalysisOption = {
  title: {
    text: "Semanas vs Informes Enviados",
    padding: [20, 0],
  },
  tooltip: {
    trigger: "axis",
  },
  legend: {
    type: "scroll",
    data: [],
  },
  yAxis: {
    type: "value",
    name: "Informes enviados",
    nameRotate: 90,
    nameGap: 50,
    nameLocation: "center",
  },
  xAxis: {
    type: "category",
    data: [],
    name: "Semanas",
    nameGap: 50,
    nameLocation: "center",
  },
  series: [],
};

let totalsResponseTimeOption = {
  title: {
    text: "Tiempo en dias por etapa de servicio",
  },
  tooltip: {
    trigger: "axis",
  },
  radar: {
    indicator: [
      { name: "Procesamiento", max: 10 },
      { name: "Derivacion", max: 10 },
      { name: "Espera", max: 10 },
      { name: "Lectura", max: 10 },
      { name: "Revision", max: 10 },
    ],
  },
  series: [],
};

function getResponseChartData() {
  const date_start = $("#dateStartResponse").val();
  const date_end = $("#dateEndResponse").val();
  const pathologists = $("#pathologistsResponse")
    .select2("data")
    .map((selected) => selected.id)
    .join(";");
  const areas = $("#areasResponse")
    .select2("data")
    .map((selected) => selected.id)
    .join(";");
  const requestData = {
    date_start,
    date_end,
    pathologists,
    areas,
  };
  $.ajax({
    url: Urls["report:control_response_charts"](),
    data: requestData,
  }).done((data) => {
    initializeResponseCharts(data);
  });
}

function initializeResponseCharts(data) {
  weeklyDaysResponseChartInit(data);
  weeklyAnalysisChartInit(data);
  totalsResponseTimeChartInit(data);
}

function weeklyDaysResponseChartInit(data) {
  const dataByWeek = _.groupBy(data, (analysis) => analysis.week);

  let weeksData = [];

  let processingDays = [];
  let assigningDays = [];
  let waitingDays = [];
  let readingDays = [];
  let reviewingDays = [];
  for (const week in dataByWeek) {
    let sumProcessingDays = 0;
    let countProcessingDays = 0;

    let sumAssigningDays = 0;
    let countAssigningDays = 0;

    let sumWaitingDays = 0;
    let countWaitingDays = 0;

    let sumReadingDays = 0;
    let countReadingDays = 0;

    let sumReviewingDays = 0;
    let countReviewingDays = 0;

    for (const analysis of dataByWeek[week]) {
      if (analysis.days_processing >= 0) {
        countProcessingDays++;
        sumProcessingDays += analysis.days_processing;
      }

      if (analysis.days_assigning >= 0) {
        countAssigningDays++;
        sumAssigningDays += analysis.days_assigning;
      }

      if (analysis.days_waiting >= 0) {
        countWaitingDays++;
        sumWaitingDays += analysis.days_waiting;
      }

      if (analysis.days_reading >= 0) {
        countReadingDays++;
        sumReadingDays += analysis.days_reading;
      }

      if (analysis.days_reviewing >= 0) {
        countReviewingDays++;
        sumReviewingDays += analysis.days_reviewing;
      }
    }

    const currentWeekProcessingDays = Math.round(
      sumProcessingDays / countProcessingDays
    );
    const currentWeekAssigningDays = Math.round(
      sumAssigningDays / countAssigningDays
    );
    const currentWeekWaitingDays = Math.round(
      sumWaitingDays / countWaitingDays
    );
    const currentWeekReadingDays = Math.round(
      sumReadingDays / countReadingDays
    );
    const currentWeekReviewingDays = Math.round(
      sumReviewingDays / countReviewingDays
    );

    processingDays.push(currentWeekProcessingDays);
    assigningDays.push(currentWeekAssigningDays);
    waitingDays.push(currentWeekWaitingDays);
    readingDays.push(currentWeekReadingDays);
    reviewingDays.push(currentWeekReviewingDays);
  }

  let series = [
    {
      name: "Procesamiento",
      type: "line",
      stack: "weekly",
      areaStyle: {},
      data: processingDays,
    },
    {
      name: "Derivacion",
      type: "line",
      stack: "weekly",
      areaStyle: {},
      data: assigningDays,
    },
    {
      name: "Espera",
      type: "line",
      stack: "weekly",
      areaStyle: {},
      data: waitingDays,
    },
    {
      name: "Lectura",
      type: "line",
      stack: "weekly",
      areaStyle: {},
      data: readingDays,
    },
    {
      name: "Revision",
      type: "line",
      stack: "weekly",
      areaStyle: {},
      data: reviewingDays,
    },
  ];

  weeklyDaysResponseOption.xAxis.data = Object.keys(dataByWeek);
  weeklyDaysResponseOption.series = series;

  weeklyDaysResponseChart.setOption(weeklyDaysResponseOption, true);
}

function weeklyAnalysisChartInit(data) {
  const dataByUser = _.groupBy(data, (analysis) => analysis.user);
  const responseWeeks = extractWeeks(data).sort();

  let series = [];
  for (const user in dataByUser) {
    let serie = {
      name: user,
      type: "bar",
      stack: "chart",
      data: [],
    };
    const dataByUserWeek = _.groupBy(
      dataByUser[user],
      (analysis) => analysis.week
    );

    for (const week of responseWeeks) {
      let weekCount = 0;
      if (dataByUserWeek[week]) {
        weekCount = dataByUserWeek[week].length;
      }
      serie.data.push(weekCount);
    }

    series.push(serie);
  }

  weeklyAnalysisOption.legend.data = Object.keys(dataByUser);
  weeklyAnalysisOption.xAxis.data = responseWeeks;
  weeklyAnalysisOption.series = series;

  weeklyAnalysisChart.setOption(weeklyAnalysisOption, true);
}

function totalsResponseTimeChartInit(data) {
  let sumProcessingDays = 0;
  let countProcessingDays = 0;

  let sumAssigningDays = 0;
  let countAssigningDays = 0;

  let sumWaitingDays = 0;
  let countWaitingDays = 0;

  let sumReadingDays = 0;
  let countReadingDays = 0;

  let sumReviewingDays = 0;
  let countReviewingDays = 0;

  for (const analysis of data) {
    if (analysis.days_processing >= 0) {
      countProcessingDays++;
      sumProcessingDays += analysis.days_processing;
    }

    if (analysis.days_assigning >= 0) {
      countAssigningDays++;
      sumAssigningDays += analysis.days_assigning;
    }

    if (analysis.days_waiting >= 0) {
      countWaitingDays++;
      sumWaitingDays += analysis.days_waiting;
    }

    if (analysis.days_reading >= 0) {
      countReadingDays++;
      sumReadingDays += analysis.days_reading;
    }

    if (analysis.days_reviewing >= 0) {
      countReviewingDays++;
      sumReviewingDays += analysis.days_reviewing;
    }
  }

  const avgProcessingDays = Math.round(sumProcessingDays / countProcessingDays);
  const avgAssigningDays = Math.round(sumAssigningDays / countAssigningDays);
  const avgWaitingDays = Math.round(sumWaitingDays / countWaitingDays);
  const avgReadingDays = Math.round(sumReadingDays / countReadingDays);
  const avgReviewingDays = Math.round(sumReviewingDays / countReviewingDays);

  totalsResponseTimeOption.series = [
    {
      type: "radar",
      tooltip: {
        trigger: "item",
      },
      areaStyle: {},
      data: [
        {
          value: [
            avgProcessingDays,
            avgAssigningDays,
            avgWaitingDays,
            avgReadingDays,
            avgReviewingDays,
          ],
          name: "Tiempo de Respuesta",
        },
      ],
    },
  ];

  totalsResponseTimeChart.setOption(totalsResponseTimeOption, true);
}

$(document).ready(() => {
  getResponseChartData();
});

$(".filterInputResponse").on("input select2:select select2:deselect", () => {
  getResponseChartData();
});
