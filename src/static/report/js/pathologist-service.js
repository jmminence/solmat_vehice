function deltaDay(first, second) {
  return Math.round((second - first) / (1000 * 60 * 60 * 24));
}

$(document).ready(() => {
  $(".select2").select2();

  $("#pendingTable").DataTable({
    processing: true,
    serverSide: true,
    ajax: {
      url: Urls["report:services_table"](),
      data: (request) => {
        const pathologists = $("#pathologistPending").select2("data");
        let selected_pathologists = [];
        for (const pathologist of pathologists) {
          selected_pathologists.push(pathologist.id);
        }
        const areas = $("#areaPending").select2("data");
        let selected_area = [];
        for (const area of areas) {
          selected_area.push(area.id);
        }

        request.pathologists = selected_pathologists.join(";");
        request.areas = selected_area.join(";");

        request.table = "PENDING";
      },
    },

    columns: [
      { data: "case.no_caso", title: "Caso" },
      { data: "customer.name", title: "Cliente" },
      {
        data: "exam.name",
        title: "Servicio",
        render: (data) => {
          if (data) {
            return data;
          }
          return "";
        },
      },
      { data: "stain.abbreviation", title: "Tinción" },
      {
        data: "pathologist",
        title: "Patólogo",
        render: (data) => {
          return `${data.first_name} ${data.last_name}`;
        },
      },
      { data: "samples_count", title: "# Muestras" },
      {
        data: "case.created_at",
        title: "Recepcion",
        render: (data) => {
          const date = new Date(data);
          return date.toLocaleDateString();
        },
      },
      {
        data: "service.assignment_done_at",
        title: "Derivacion",
        render: (data) => {
          const date = new Date(data);
          return date.toLocaleDateString();
        },
      },
      {
        data: "deadline",
        title: "Plazo",
        render: (data) => {
          const date = new Date(data);
          date.setDate(date.getDate()+1)
          return date.toLocaleDateString();
        },
      },
      {
        data: "deadline",
        title: "Atraso",
        render: (data) => {
          const date = new Date(data);
          const today = new Date();
          const deltaDays = Math.max(0, deltaDay(date, today)-1);
          return deltaDays;
        },
      },
    ],
  });

  $("#readingTable").DataTable({
    processing: true,
    serverSide: true,
    ajax: {
      url: Urls["report:services_table"](),
      data: (request) => {
        const pathologists = $("#pathologistReading").select2("data");
        let selected_pathologists = [];
        for (const pathologist of pathologists) {
          selected_pathologists.push(pathologist.id);
        }
        const areas = $("#areaReading").select2("data");
        let selected_area = [];
        for (const area of areas) {
          selected_area.push(area.id);
        }

        request.pathologists = selected_pathologists.join(";");
        request.areas = selected_area.join(";");

        request.table = "READING";
      },
    },

    columns: [
      { data: "case.no_caso", title: "Caso" },
      { data: "customer.name", title: "Cliente" },
      { data: "exam.name", title: "Servicio" },
      { data: "stain.abbreviation", title: "Tinción" },
      {
        data: "pathologist",
        title: "Patólogo",
        render: (data) => {
          return `${data.first_name} ${data.last_name}`;
        },
      },
      { data: "samples_count", title: "# Muestras" },
      {
        data: "case.created_at",
        title: "Recepcion",
        render: (data) => {
          const date = new Date(data);
          return date.toLocaleDateString();
        },
      },
      {
        data: "service.assignment_done_at",
        title: "Derivacion",
        render: (data) => {
          const date = new Date(data);
          return date.toLocaleDateString();
        },
      },
      {
        data: "deadline",
        title: "Plazo",
        render: (data) => {
          const date = new Date(data);
          date.setDate(date.getDate()+1)
          return date.toLocaleDateString();
        },
      },
      {
        data: "service.pre_report_started_at",
        title: "Inicio lectura",
        render: (data) => {
          const date = new Date(data);
          return date.toLocaleDateString();
        },
      },
      {
        data: "deadline",
        title: "Atraso",
        render: (data) => {
          const date = new Date(data);
          const today = new Date();
          const deltaDays = Math.max(0, deltaDay(date, today));
          return deltaDays;
        },
      },
      {
        data: "service.pre_report_started_at",
        title: "En lectura",
        render: (data) => {
          const date = new Date(data);
          const today = new Date();
          const deltaDays = Math.max(0, deltaDay(date, today));
          return deltaDays;
        },
      },
    ],
  });

  $("#reviewingTable").DataTable({
    processing: true,
    serverSide: true,
    ajax: {
      url: Urls["report:services_table"](),
      data: (request) => {
        const pathologists = $("#pathologistReviewing").select2("data");
        let selected_pathologists = [];
        for (const pathologist of pathologists) {
          selected_pathologists.push(pathologist.id);
        }
        const areas = $("#areaReviewing").select2("data");
        let selected_area = [];
        for (const area of areas) {
          selected_area.push(area.id);
        }

        request.pathologists = selected_pathologists.join(";");
        request.areas = selected_area.join(";");

        request.table = "REVIEWING";
      },
    },

    columns: [
      { data: "case.no_caso", title: "Caso" },
      { data: "customer.name", title: "Cliente" },
      { data: "exam.name", title: "Servicio" },
      { data: "stain.abbreviation", title: "Tinción" },
      {
        data: "pathologist",
        title: "Patólogo",
        render: (data) => {
          return `${data.first_name} ${data.last_name}`;
        },
      },
      { data: "samples_count", title: "# Muestras" },
      {
        data: "case.created_at",
        title: "Recepcion",
        render: (data) => {
          const date = new Date(data);
          return date.toLocaleDateString();
        },
      },
      {
        data: "service.pre_report_started_at",
        title: "Inicio lectura",
        render: (data) => {
          const date = new Date(data);
          return date.toLocaleDateString();
        },
      },
      {
        data: "service.pre_report_ended_at",
        title: "Fin lectura",
        render: (data) => {
          const date = new Date(data);
          return date.toLocaleDateString();
        },
      },
      {
        data: "service.pre_report_ended_at",
        title: "En revision",
        render: (data) => {
          const date = new Date(data);
          const today = new Date();
          const deltaDays = Math.max(0, deltaDay(date, today));
          return deltaDays;
        },
      },
    ],
  });

  $(".pendingInput").on("input select2:select select2:unselect", () => {
    $("#pendingTable").DataTable().ajax.reload();
  });

  $(".readingInput").on("input select2:select select2:unselect", () => {
    $("#readingTable").DataTable().ajax.reload();
  });

  $(".reviewingInput").on("input select2:select select2:unselect", () => {
    $("#reviewingTable").DataTable().ajax.reload();
  });
});
