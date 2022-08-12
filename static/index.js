$("#login").on('click', function() {
    var user = {
        username: $("#username").val(),
        password: $("#password").val()
    }
    
    

    $.ajax({
        type: "POST",
        dataType: "json",
        contentType: "application/json",
        url: "http://localhost:5000/api/login",
        processData: false,
        success: function(msg) {
            alert(JSON.stringify(msg));
        },
        data: JSON.stringify(user)
    })
});