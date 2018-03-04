authUser = {
  token: window.localStorage.getItem("token")
};

var validateToken = function(condition, callback) {
  if (authUser.token == null) {
    if (condition == false) {
      callback();
    }
    return;
  }
  // alternatively, we can be less defensive and simply check for presence of token

  var data = `{"token": "${authUser.token}"}`;

  $.ajax({
    url: "http://localhost:8080/users",
    type: "POST",
    dataType: "json",
    data: data,
    contentType: "application/json",

    success: function(response) {
      console.log(response);

      if (response.status == true) {
        authUser.username = response.result.username;
        authUser.fullname = response.result.fullname;
        authUser.age = response.result.age;

        if (condition == true) {
          callback();
        }
      } else if (response.status == false) {
        window.localStorage.removeItem("token");

        if (condition == false) {
          callback();
        }
      }
    },

    error: function(xhr, resp, text) {
      console.log(xhr, resp, text);
    }
  });
};

var verifyLoggedIn = function() {
  // redirect if user is not logged in
  validateToken(false, function() {
    alert("Please login to view this page");
    window.location.href = "index.html";
  });
};

var verifyLoggedOut = function() {
  // redirect if user is logged in
  validateToken(true, function() {
    alert("You are already logged in");
    window.location.href = "private_entries.html";
  });
};

$(document).ready(function() {
  $("#logout").on("click", function() {
    window.localStorage.removeItem("token");

    var data = `{"token": "${authUser.token}"}`;

    $.ajax({
      url: "http://localhost:8080/users/expire",
      type: "POST",
      dataType: "json",
      data: data,
      contentType: "application/json",

      success: function(response) {
        console.log(response);

        if (response.status == true) {
          alert("Successfully logged out!");
          window.location.href = "index.html";
        } else if (response.status == false) {
          alert("Already logged out!");
        }
      },

      error: function(xhr, resp, text) {
        console.log(xhr, resp, text);
      }
    });
  });
});
