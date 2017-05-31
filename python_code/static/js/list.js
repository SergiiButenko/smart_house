var server = 'http://mozart.hopto.org:7543';
//var server = 'http://127.0.0.1:7543';

var arduino_check_connect_sec = 60*5;
var arduino_check_broken_connect_sec = 60;

var branch_names = [];

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


    //Assign onClick for close buttons on Modal window
    $(".modal_close").click(function() {
        //update_branches_request();
    });

    //Function to start irrigation
    $(".start-irrigation").click(function() {
        // index = $('#time_modal').data('id');
        // time = $("#time_selector option:selected").data("value");
        // console.log(branch_names[index]+" will be activated on "+time+" minutes");
        //branch_on(index, time);
    });

});