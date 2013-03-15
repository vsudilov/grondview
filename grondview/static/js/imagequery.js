var fileExists, tolerance_requests;

tolerance_requests = 5;

fileExists = function(file, i) {
  return $.ajax(file, {
    type: 'HEAD',
    dataType: 'html',
    async: true,
    timeout: 2000,
    error: function(jqXHR, textStatus, errorThrown) {
      i += 1;
      if (i > tolerance_requests) return null;
      return setTimeout((function() {
        return fileExists(file, i, pngID);
      }), 1000);
    },
    success: function(data, textStatus, jqXHR) {
      var id;
      id = file.split('/').pop().slice(0, -4);
      return $('img.png' + id).attr('src', file);
    }
  });
};
