let users = [];
let weeks = [];
let exams = [];

$(document).ready(() => {
  $(".select2").select2();
  getChartData();
});

$(".filterInput").on("input select2:select select2:deselect", () => {
  getChartData();
});

// EFFICIENCY CHARTS

let weekOrganUserChart = echarts.init(document.getElementById("weekOrganUser"));
let servicesUserChart = echarts.init(document.getElementById("servicesUser"));
let totalsExamChart = echarts.init(document.getElementById("totalsExam"));
let totalsTimeChart = echarts.init(document.getElementById("totalsTime"));
let totalsGlobalChart = echarts.init(document.getElementById("totalsGlobal"));

let weekOrganUserOption = {
  title: {
    text: "Semanas vs Organos leidos agrupado por patologo",
    padding: [20, 20],
  },
  tooltip: {
    trigger: "item",
    formatter: "{a}: {c} organos leidos",
  },
  legend: {
    type: "scroll",
    data: [],
  },
  yAxis: {
    type: "value",
    name: "Organos leidos",
    nameLocation: "center",
    nameGap: 50,
    nameRotate: 90,
  },
  xAxis: {
    type: "category",
    name: "Semanas",
    nameLocation: "center",
    nameGap: 50,
    data: [],
  },
  series: [],
};
let servicesUserOption = {
  title: {
    text: "Patologo por servicios realizados proporcional",
    padding: [20, 0],
  },
  tooltip: {
    trigger: "item",
    formatter: "{a}: {c} %",
  },
  legend: {
    type: "scroll",
    data: [],
  },
  grid: {
    left: "3%",
    right: "4%",
    bottom: "3%",
    containLabel: true,
  },
  yAxis: {
    type: "category",
    data: [],
  },
  xAxis: {
    type: "value",
    name: "Porcentaje de Servicios Realizados",
    nameGap: 50,
    nameLocation: "center",
  },
  series: [],
};
let totalsExamOption = {
  title: {
    text: "Porcentaje de servicios totales",
    padding: [20, 0],
  },
  tooltip: {
    trigger: "item",
    formatter: "{a} <br/> {b} : {c} %",
  },
  legend: {
    type: "scroll",
    data: [],
  },
  grid: {
    left: "3%",
    right: "4%",
    bottom: "3%",
    containLabel: true,
  },
  yAxis: {
    type: "category",
    data: [],
  },
  xAxis: {
    type: "value",
  },
  series: [],
};
let totalsTimeOption = {
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
    ],
  },
  series: [],
};
let totalsGlobalOption = {
  title: {
    text: "Totales",
  },
  tooltip: {
    trigger: "item",
    formatter: "{a} <br/>{b} : {c}",
  },
  series: [],
};

function getChartData() {
  const date_start = $("#dateStart").val();
  const date_end = $("#dateEnd").val();
  const pathologists = $("#pathologists")
    .select2("data")
    .map((selected) => selected.id)
    .join(";");
  const areas = $("#areas")
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
    url: Urls["report:control_efficiency_charts"](),
    data: requestData,
  }).done((data) => {
    users = extractUsers(data);
    weeks = extractWeeks(data);
    exams = extractExams(data);
    initCharts(data);
  });
}

function initCharts(data) {
  const dataByUser = _.groupBy(data, (analysis) => {
    return analysis.user;
  });

  const dataByExam = _.groupBy(data, (analysis) => {
    return analysis.exam;
  });

  weekOrganUserChartInit(dataByUser);
  servicesUserChartInit(dataByExam, dataByUser);
  totalExamsChartInit(dataByExam);
  responseTimeChartInit(data);
  totalGlobalsChartInit(data);
}

function weekOrganUserChartInit(dataByUser) {
  // Format data for use in weekOrganUser chart
  // The array must first be divided by the users
  // Then it must contain for each week the sum
  // of organ, leaving 0 if there's no data
  // for that week for that user.
  let userData = {};
  for (const user in dataByUser) {
    userData[user] = {};

    let userWeek = _.groupBy(dataByUser[user], (analysis) => {
      return analysis.week;
    });

    // For every user, there's a base value of
    // 0 for every week in the date range.
    for (const week of weeks) {
      let totalOrgans = 0;
      if (userWeek[week]) {
        for (const analysis of userWeek[week]) {
          totalOrgans = totalOrgans + analysis.organs;
        }
      }
      userData[user][week] = totalOrgans;
    }
  }

  let series = [];
  for (const user in userData) {
    let serie = {
      name: user,
      type: "bar",
      stack: "users",
      data: Object.values(userData[user]),
    };
    series.push(serie);
  }

  weekOrganUserOption.xAxis.data = weeks;
  weekOrganUserOption.legend.data = users;
  weekOrganUserOption.series = series;

  weekOrganUserChart.setOption(weekOrganUserOption, true);
}

function servicesUserChartInit(dataByExam, dataByUser) {
  // Format data for use in servicesUser chart
  // The array must be divided by each user
  // and then every row inside contains the percent
  // for every service, defaulting to 0 if not present
  // for that user

  let series = [];

  servicesUserOption.yAxis.data = users;
  for (const exam in dataByExam) {
    let dataUsers = _.groupBy(dataByExam[exam], (analysis) => {
      return analysis.user;
    });

    let serie = {
      name: exam,
      type: "bar",
      stack: "exams",
      data: [],
    };

    for (const user of users) {
      const totalExams = dataByUser[user].length;
      if (dataUsers[user]) {
        let exam = dataUsers[user].length;
        let percent = (exam / totalExams) * 100;
        serie.data.push(Math.round(percent));
      } else {
        serie.data.push(0);
      }
    }

    series.push(serie);
  }

  servicesUserOption.series = series;
  servicesUserOption.legend.data = exams;
  servicesUserChart.setOption(servicesUserOption, true);
}

function totalExamsChartInit(dataByExam) {
  let totalExams = 0;
  for (const exam of exams) {
    totalExams += dataByExam[exam].length;
  }

  let data = Object.keys(dataByExam).map((exam) => {
    const percent = (dataByExam[exam].length / totalExams) * 100;
    const value = Math.round(percent);
    const name = exam;
    return {
      name,
      value,
    };
  });
  let series = [
    {
      name: "Servicios Totales",
      type: "pie",
      center: ["50%", "60%"],
      label: {
        show: false,
        position: "center",
      },
      labelLine: {
        show: false,
      },
      data: data,
    },
  ];

  totalsExamOption.legend.data = exams;
  totalsExamOption.series = series;

  totalsExamChart.setOption(totalsExamOption, true);
}

function responseTimeChartInit(data) {
  let totalWeight = 0;
  for (const row of data) {
    totalWeight = totalWeight + row.organs;
  }

  let weightedSumProcessingDays = 0;
  let processingDaysCount = 0;

  let weightedSumAssigningDays = 0;
  let assigningDaysCount = 0;

  let weightedSumWaitingDays = 0;
  let waitingDaysCount = 0;

  let weightedSumReadingDays = 0;
  let readingDaysCount = 0;

  for (const row of data) {
    if (row.days_processing >= 0) {
      processingDaysCount++;
      weightedSumProcessingDays += row.days_processing;
    }

    if (row.days_assigning >= 0) {
      assigningDaysCount++;
      weightedSumProcessingDays += row.days_assigning;
    }

    if (row.days_waiting >= 0) {
      waitingDaysCount++;
      weightedSumWaitingDays += row.days_waiting;
    }

    if (row.days_reading >= 0) {
      readingDaysCount++;
      weightedSumReadingDays += row.days_reading;
    }
  }

  const avgProcessingDays = Math.round(
    weightedSumProcessingDays / processingDaysCount
  );
  const avgAssigningDays = Math.round(
    weightedSumAssigningDays / assigningDaysCount
  );
  const avgWaitingDays = Math.round(weightedSumWaitingDays / waitingDaysCount);
  const avgReadingDays = Math.round(weightedSumReadingDays / readingDaysCount);

  totalsTimeOption.series = [
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
          ],
          name: "Tiempo de Respuesta",
        },
      ],
    },
  ];

  totalsTimeChart.setOption(totalsTimeOption, true);
}

function totalGlobalsChartInit(data) {
  let totalOrgan = 0;
  for (const row of data) {
    totalOrgan = totalOrgan + row.organs;
  }

  totalsGlobalOption.series = [
    {
      name: "Valores Absolutos",
      type: "funnel",
      sort: "descending",
      gap: 2,
      label: {
        show: true,
        position: "inside",
      },
      labelLine: {
        length: 10,
        lineStyle: {
          width: 1,
          type: "solid",
        },
      },
      itemStyle: {
        borderColor: "#fff",
        borderWidth: 1,
      },
      emphasis: {
        label: {
          fontSize: 20,
        },
      },
      data: [
        { value: totalOrgan, name: "Organos Leidos" },
        { value: data.length, name: "Analisis Realizados" },
        { value: exams.length, name: "Servicios Realizados" },
        { value: users.length, name: "Patologos" },
      ],
    },
  ];

  totalsGlobalChart.setOption(totalsGlobalOption, true);
}

function extractUsers(data) {
  let users = [];

  for (const analysis of data) {
    if (!users.includes(analysis.user)) {
      users.push(analysis.user);
    }
  }

  return users;
}

function extractExams(data) {
  let exams = [];

  for (const analysis of data) {
    if (!exams.includes(analysis.exam)) {
      exams.push(analysis.exam);
    }
  }

  return exams;
}

function extractWeeks(data) {
  let weeks = [];

  for (const analysis of data) {
    if (!weeks.includes(analysis.week)) {
      weeks.push(analysis.week);
    }
  }

  return weeks.sort();
}
