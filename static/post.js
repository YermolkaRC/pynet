$("#post").on('click', function() {
    var user = {
        post_name: $("#post_name").val(),
        post_text: $("#post_text").val()
    };
    
    $.ajax({
        type: "POST",
        dataType: "json",
        contentType: "application/json",
        url: "http://localhost:5000/api/postwithlogin",
        processData: false,
        success: function(msg) {
            alert(JSON.stringify(msg));
        },
        data: JSON.stringify(user)
    })
})