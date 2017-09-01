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
                $(".dropdown-menu").append(
                    $('<button> type="button" data-id=0 </button>')
                    .data('id', item['id'])
                    .html(item['name'])
                    .addClass("dropdown-item")                    
                    );
            }
        }
    });

    $(".dropdown-item").click(function() {
        id = $(this).data('id')
        
        default_time = branch[id]['default_time'] 
        default_interval = branch[id]['default_interval'] 
        default_time_wait = branch[id]['default_time_wait']

        $(this).parents(".dropdown").find('.btn').html($(this).text() + ' <span class="caret"></span>');

        card=$(".dropdown-item").closest(".card")
        card.data('id', id);
        card.find('#irrigation_minutes').val(default_time);
        card.find('#irrigation_intervals').val(default_interval);
        card.find('#irrigation_time_wait').val(default_time_wait);
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