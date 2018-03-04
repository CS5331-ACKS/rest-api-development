
    $(document).ready(function(){
         // click on button submit
        $("#submit").on('click', function(e){

          e.preventDefault();
          e.returnValue = false;

          var userVar = document.getElementById("username").value;
          var pwdVar = document.getElementById("password").value;
          var formData = `{\"username\": "${userVar}",\"password\": "${pwdVar}"}`;


          if (document.getElementById("username").value == "" || document.getElementById("password").value == "")
          {
            alert("Please fill up all the fields");
            return;
          }

            // send ajax
            $.ajax({
                url: 'http://localhost:8080/users/authenticate', // url where to submit the request
                type : "POST", // type of action POST || GET
                dataType : 'json', // data type
                data : formData,
                contentType: "application/json",
                success : function(response) {

                    //console.log(response);
                    //callback(result.token);

                    if (response.status == true)
                    {
                      
                      return_first = response.result.token;
                      alert("Login successful!");
                      window.localStorage.setItem('token', return_first);
                      window.location.href = 'userhome.html';
                    }

                    else if (response.status == false)
                    {
                      alert("Login failed. Please try again.");

                    }


                },
                error: function(xhr, resp, text) {
                    console.log(xhr, resp, text);
                }
            })


        });


    });
