$(document).ready(function() {
	$(".signuppage").click(function() {
		mixpanel.track("signuppage");
	    });

	$(".create").click(function() {
		mixpanel.track("account created");
	    });
	

    });