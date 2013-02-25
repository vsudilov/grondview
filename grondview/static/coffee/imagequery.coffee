tolerance_requests = 5
fileExists = (file,i,pngID) -> $.ajax file,
    type: 'HEAD'
    dataType: 'html'
    async: true
    timeout: 2000
    error: (jqXHR, textStatus, errorThrown) ->
        i+=1        
        if i>tolerance_requests
          return null
        setTimeout (-> fileExists file,i,pngID), 1000
    success: (data, textStatus, jqXHR) ->
        $('img.png'+pngID).attr('src',file)
