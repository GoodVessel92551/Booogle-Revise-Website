const notification_fun = (text) => {
    if ('Notification' in window) {
      Notification.requestPermission()
        .then(function (permission) {
          if (permission === 'granted') {
            var notification = new Notification('Hello, World!', {
              body: text,
              icon: "/static/logo.png"
            });
            notification.onclick = function () {
              console.log('Notification clicked');
            };
          }
        })
        .catch(function (error) {
          console.error('Notification permission denied:', error);
        });
    } else {
      console.error('Notification API is not supported in this browser.');
    }
}