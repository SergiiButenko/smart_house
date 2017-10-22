var server = location.protocol + '//' + location.hostname + (location.port ? ':' + location.port : '');

$(document).ready(function() {
    //Add arduino touch script to determine if connection is alive

    (function() {
        state = $("#all_rules").is(":checked")
        $('#rules_table tr td:nth-child(2)').each(function() {
            if (($(this).text().indexOf("Остановить") != -1 || $(this).text().indexOf("Зупинити") != -1) & !state)
                $(this).closest("tr").hide();

            if (($(this).text().indexOf("Остановить") != -1 || $(this).text().indexOf("Зупинити") != -1) & state)
                $(this).closest("tr").show();
        });
    })();

    $(".btn-refresh-history").click(function() {
        $.ajax({
            url: '/list_all',
            type: "get",
            data: {
                'days': $(this).data('value'),
            },
            success: function(data) {
                $('#rules_table').html(data);
            }
        });
    });

    $("#all_rules").change(function() {
        state = $("#all_rules").is(":checked")
        $('#rules_table tr td:nth-child(2)').each(function() {
            if (($(this).text().indexOf("Остановить") != -1 || $(this).text().indexOf("Зупинити") != -1) & !state)
                $(this).closest("tr").hide();

            if (($(this).text().indexOf("Остановить") != -1 || $(this).text().indexOf("Зупинити") != -1) & state)
                $(this).closest("tr").show();
        });
    });
});