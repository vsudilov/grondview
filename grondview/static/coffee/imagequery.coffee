###
fileExists = (location) $ -> $.ajax(
  url: location
  type: 'HEAD'
  error: -> $('p').text("failure") 
  success: -> $('p').text("success"))

fileExists("{{ MEDIA_URL }}{{ image.RAW_PNG }}")
###

myFun = (msg) -> 
  towrite = msg
  $('p').text(towrite)
  
###
fileExists = $.get(para)
  .success (response) ->
    $('p').text("Reponse recieved")
  .error (response) ->
    $('p').text("Not yet there...")
###

###
fileExists = $.ajax "test",
    type: 'HEAD'
    dataType: 'html'
    async: true
    error: (jqXHR, textStatus, errorThrown) ->
        $('p').append "AJAX Error: #{textStatus} #{errorThrown}"
        fileExists
    success: (data, textStatus, jqXHR) ->
        $('p').append "Successful AJAX call: #{data}"    
###  

updateInterval = 5000
fileExists = (file) -> $.ajax file,
    type: 'HEAD'
    dataType: 'html'
    async: true
    timeout: 3000
    error: (jqXHR, textStatus, errorThrown) ->
        return null
    success: (data, textStatus, jqXHR) ->
        $('img').attr('src',file)
        clearInterval(int_id)
        
#int_id = setInterval fileExists, updateInterval