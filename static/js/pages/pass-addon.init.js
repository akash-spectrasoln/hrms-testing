// Toggle visibility for the main password
document.getElementById("password-addon").addEventListener("click", function () {
    var passwordInput = document.getElementById("password-input");
    if (passwordInput.type === "password") {
        passwordInput.type = "text";
    } else {
        passwordInput.type = "password";
    }
});

// Toggle visibility for the confirm password
document.getElementById("password-addon1").addEventListener("click", function () {
    var confirmPasswordInput = document.getElementById("password-input1");
    if (confirmPasswordInput.type === "password") {
        confirmPasswordInput.type = "text";
    } else {
        confirmPasswordInput.type = "password";
    }
});