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

    //Function to start irrigation
    $(".deactivate_rules").click(function() {        
        id = $("#rule_selector option:selected").data("value");
        $.ajax({
            url: server+'/deactivate_all_rules',
            type: "get",
            data: {
                'id': id
            },
            success: function(data) {
                if (id != 3) 
                    location.reload();
                
            }
        });
    });
});

    function activate_rule(that){
        id = $(that).data('id');
        $.ajax({
            url: server+'/activate_rule',
            type: "get",
            data: {
                'id': id
            },
            success: function(data) {
                   
            }
        });
    }

    function deactivate_rule(that){
        id = $(that).data('id');
        $.ajax({
            url: server+'/deactivate_rule',
            type: "get",
            data: {
                'id': id
            },
            success: function(data) {
                   
            }
        });
    }