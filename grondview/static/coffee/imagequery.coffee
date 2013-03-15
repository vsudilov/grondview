tolerance_requests = 5
fileExists = (file,i) -> $.ajax file,
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
        id = file.split('/').pop().slice(0,-4)
        $('img.png'+id).attr('src',file)
