var server = 'http://127.0.0.1:7543';

$(document).ready(function() {

    var $loading = $('#loader').hide();
    $(document)
        .ajaxStart(function() {
            $loading.show();
        })
        .ajaxStop(function() {
            $loading.hide();
    });
      

    touch_analog_sensor();

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

    //Add arduino touch script to determine if connection is alive
    (function humidity_sensor() {
        $.ajax({
            url: server+'/humidity_sensor',
            success: function(data) {
                $("#humidity_span").text(data['tank_sensor']);
                $("#humidity_text").text(data['text']);
                humidity_text
                setTimeout(humidity_sensor, 10 * 1000 * 30);
            },
            global:false
        });
    })();

    
});


function touch_analog_sensor(){
    $.ajax({
            url: server+'/humidity_sensor',
            success: function(data) {
                $("#humidity_span").text(data['tank_sensor']);
                $("#humidity_text").text(data['text']);
            }
        });
}
