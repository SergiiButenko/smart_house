var server = location.protocol + '//' + location.hostname + (location.port ? ':' + location.port : '');
var branch = [];

$(document).ready(function() {
    //Rename branches
    $.ajax({
        url: server + '/branches_names',
        success: function(data) {
            list = data['list']
            for (j in list) {
                item = list[j]
                branch[item['id']] = {
                    'name': item['name'],
                    'default_time': parseInt(item['default_time']) || 10,
                    'default_interval': parseInt(item['default_interval']) || 2,
                    'default_time_wait': parseInt(item['default_time_wait']) || 15
                }
                 $(".branch_dropdown").append( $('<li></li>').val('id', item['id']).html(item['name']))                
            }
        }
    });


    $("#add_rule_block").click(function() {
        element = $(".card_to_copy").children();
        $(".card-group").append(element.clone().show());
        $(".remove_card").click(function() {
            $(this).parent().parent().remove();
        });
    });

    $(".remove_card").click(function() {
        $(this).parent().parent().remove();
    });
});