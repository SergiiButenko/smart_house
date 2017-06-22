var server = 'http://185.20.216.94:7543'; 
//var server = 'http://127.0.0.1:7543';

$(document).ready(function() {
    var $loading = $('#loader').hide();
    $(document)
        .ajaxStart(function() {
            $loading.show();
        })
        .ajaxStop(function() {
            $loading.hide();
    });
    
    //Add arduino touch script to determine if connection is alive
    (function update_weather() {
        $.ajax({
            url: server+'/weather',
            success: function(data) {
                $("#temp_header").text("Температура воздуха: " + data['temperature'] + " C*");
                setTimeout(update_weather, 60 * 1000 * 30);
            },
            global:false
        });
    })();

    $(".btn-refresh-history").click(function(){
        $.ajax({
                             url: server + '/list_all',
                             type: "get",
                             data: {
                                 'days': $(this).data('value'),
                             },
                             success: function(data) {
                                 $('#rules_table').html(data);
                             }
                             });
    });
});