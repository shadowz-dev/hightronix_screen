var applicationID = '81585E3E';
var namespace = 'urn:x-cast:com.jrk.obscreen';
var session = null;

if (!chrome.cast || !chrome.cast.isAvailable) {
    setTimeout(initializeCastApi, 1000);
}

function initializeCastApi() {
    var sessionRequest = new chrome.cast.SessionRequest(applicationID);
    var apiConfig = new chrome.cast.ApiConfig(sessionRequest,
        sessionListener,
        receiverListener);

    chrome.cast.initialize(apiConfig, onInitSuccess, onError);
}

function onInitSuccess() {
    // console.log('onInitSuccess');
}

function onError(message) {
    console.error('onError: ' + JSON.stringify(message));
}

function onSuccess(message) {
    // console.log('onSuccess: ' + JSON.stringify(message));
}

// function onStopAppSuccess() {
// console.log('onStopAppSuccess');
// }

function sessionListener(e) {
    console.log('New session ID: ' + e.sessionId);
    session = e;
    session.addUpdateListener(sessionUpdateListener);
}

function sessionUpdateListener(isAlive) {
    console.log((isAlive ? 'Session Updated' : 'Session Removed') + ': ' + session.sessionId);
    if (!isAlive) {
        session = null;
    }
}

function receiverListener(e) {
    // Due to API changes just ignore this.
}

function sendMessage(message) {
    if (session != null) {
        session.sendMessage(namespace, message, onSuccess.bind(this, message), onError);
    } else {
        chrome.cast.requestSession(function (e) {
            session = e;
            sessionListener(e);
            session.sendMessage(namespace, message, onSuccess.bind(this, message), onError);
        }, onError);
    }
}

// function stopApp() {
//     session.stop(onStopAppSuccess, onError);
// }

jQuery(function ($) {
    $(document).on('click', '.cast-url', function () {
        sendMessage({
            type: 'load',
            url: $('#' + $(this).attr('data-target-id')).val()
        });
    });
});