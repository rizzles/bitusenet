$(document).ready(function() {
	$(".signuppage").click(function() {
		mixpanel.track("signuppage");
		console.log('test');
		return false;
	    });

	$(".create").click(function() {
		mixpanel.track("account created");
	    });
	

    });