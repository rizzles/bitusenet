$(document).ready(function() {
	$(".signuppage").click(function() {
		mixpanel.track("signup page clicked");
	    });

	$(".create").click(function() {
		mixpanel.track("account created");
	    });
	

    });