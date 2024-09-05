$(document).ready(function () {
    /* VARIABLES */
    const dlgEdit = new bootstrap.Modal(document.getElementById("dlgEdit"));
    const dlgCreate = new bootstrap.Modal(document.getElementById("dlgCreate"));

    const newSelUnit = $("#newSelectUnit");
    const newBuildDate = $("#newBuildDate");
    const newStain = $("#newStain");

    newSelUnit.select2({
        width: "100%",
        dropdownParent: $("#dlgCreate"),
        ajax: {
            url: Urls["lab:unit_select_options"](),
            dataType: "json",
            delay: 250,
            data: (params) => {
                var query = {
                    search: params.term,
                    page: params.page || 1,
                    cassettes: true,
                };

                // Query parameters will be ?search=[term]&page=[page]&cassettes=true
                return query;
            },
        },
    });

    const editStain = $("#editStain");
    const correlative = $("#correlative");
    const buildDate = $("#buildDate");

    // var stains is declared and assigned in templates/slides/index.html
    let slide;
    let stains;

    $.get(Urls["lab:stain_index"](), (data) => {
        stains = data;
        const options = stains.map((stain) => {
            return {
                id: stain.pk,
                text: stain.fields.abbreviation,
            };
        });
        editStain.select2({
            data: options,
            width: "100%",
            dropdownParent: $("#dlgEdit"),
        });
        newStain.select2({
            data: options,
            width: "100%",
            dropdownParent: $("#dlgCreate"),
        });
    });

    const tableIndex = $(".zero-configuration").DataTable({
        oLanguage: {
            sUrl:
                "https://cdn.datatables.net/plug-ins/1.10.16/i18n/Spanish.json",
        },

        rowsGroup: [0, 1, 2],
    });

    /* END VARIABLES */

    /* FUNCTIONS */

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

    function getIdFromClassList(classList) {
        // Turn the event target's classList into an array
        const id = [...classList]
            // Find among the classes the one containing the id using regex
            .find((value) => /^id-/.test(value))
            // Split the class into 2 using `-` as separator and
            // get second part of the class containing the id
            .split("-")[1];
        return id;
    }

    /* END FUNCTIONS */

    /*  EVENTS  */

    $(".btnEdit").click((e) => {
        const id = getIdFromClassList(e.target.classList);

        $.get(Urls["lab:slide_detail"](id), (data) => {
            slide = data[0];

            correlative.val(slide.fields.correlative);
            editStain.val(slide.fields.stain).trigger("change");
            buildDate.val(slide.fields.build_at);
        });

        dlgEdit.show();
    });

    $(".btn-close").click(() => {
        dlgEdit.hide();
        dlgCreate.hide();
    });

    $("#btnSave").click(() => {
        const correlative_value = correlative.val();
        const stainValue = editStain.select2("data")[0].id;
        const buildDateValue = buildDate.val();

        $.ajax(Urls["lab:slide_detail"](slide.pk), {
            data: JSON.stringify({
                build_at: buildDateValue,
                correlative: correlative_value,
                stain_id: stainValue,
            }),

            method: "POST",

            headers: {
                "X-CSRFToken": getCookie("csrftoken"),
            },

            contentType: "application/json; charset=utf-8",

            success: (data, textStatus) => {
                slide = null;
                correlative.val("");
                buildDate.val("");
                Swal.fire({
                    icon: "success",
                    title: "Guardado",
                }).then(() => {
                    location.reload();
                });
            },

            error: (xhr, textStatus, error) => {
                Swal.fire({
                    icon: "error",
                });
            },
        });
    });

    $("#btnCreate").click(() => {
        dlgCreate.show();
    });

    $("#btnSaveNew").click(() => {
        const selectedUnit = newUnit.select2("data")[0].id;
        const unit = selectedUnit.split(".");
        const build_at = newBuildDate.val();
        const stain = newStain.select2("data")[0].id;

        // type will be either cassette_id or unit_id according to the id's model
        let type = `${unit[1]}_id`;

        let post = {
            build_at: build_at,
            slides: [
                {
                    stain_id: stain,
                },
            ],
        };

        post.slides[0][type] = unit[2];

        $.ajax(Urls["lab:slide_build"](), {
            data: JSON.stringify(post),

            method: "POST",

            headers: {
                "X-CSRFToken": getCookie("csrftoken"),
            },

            contentType: "application/json; charset=utf-8",

            success: (data, textStatus) => {
                slide = null;
                newBuildDate.val("");
                newUnit.val(null).trigger("change");

                Swal.fire({
                    icon: "success",
                    title: "Guardado",
                }).then(() => {
                    location.reload();
                });
            },

            error: (xhr, textStatus, error) => {
                Swal.fire({
                    icon: "error",
                });
            },
        });
    });

    /* END EVENTS  */
});
