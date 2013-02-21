/*
fileExists = (location) $ -> $.ajax(
  url: location
  type: 'HEAD'
  error: -> $('p').text("failure") 
  success: -> $('p').text("success"))

fileExists("{{ MEDIA_URL }}{{ image.RAW_PNG }}")
*/
var fileExists, myFun, updateInterval;

myFun = function(msg) {
  var towrite;
  towrite = msg;
  return $('p').text(towrite);
};

/*
fileExists = $.get(para)
  .success (response) ->
    $('p').text("Reponse recieved")
  .error (response) ->
    $('p').text("Not yet there...")
*/

/*
fileExists = $.ajax "test",
    type: 'HEAD'
    dataType: 'html'
    async: true
    error: (jqXHR, textStatus, errorThrown) ->
        $('p').append "AJAX Error: #{textStatus} #{errorThrown}"
        fileExists
    success: (data, textStatus, jqXHR) ->
        $('p').append "Successful AJAX call: #{data}"
*/

updateInterval = 5000;

fileExists = function(file) {
  return $.ajax(file, {
    type: 'HEAD',
    dataType: 'html',
    async: true,
    timeout: 3000,
    error: function(jqXHR, textStatus, errorThrown) {
      return null;
    },
    success: function(data, textStatus, jqXHR) {
      $('img').attr('src', file);
      return clearInterval(int_id);
    }
  });
};
