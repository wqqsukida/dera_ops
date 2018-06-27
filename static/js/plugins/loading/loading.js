jQuery.bootstrapLoading = {
  start: function (options) {
    var defaults = {
      opacity: 1,
      backgroundColor: "#fff",
      borderColor: "#bbb",
      borderWidth: 5,
      borderStyle: "solid",
      loadingTips: "Loading, please wait...",
      TipsColor: "#666",
      delayTime: 1000,
      zindex: 2051,   // 要比遮罩层的大，遮罩层为2050
      sleep: 0
    };
    var options = $.extend(defaults, options);
    var _PageHeight = document.documentElement.clientHeight;
    var _PageWidth = document.documentElement.clientWidth;
    var _LoadingHtml = '<div id="loadingPage" style="position:fixed;left:0;top:0;_position: absolute;width:100%;height:' + _PageHeight + 'px' + ';opacity:' + options.opacity + ';filter:alpha(opacity=' + options.opacity * 100 + ');z-index:' + options.zindex + ';"><div id="loadingTips" style="position: absolute; cursor: wait; width: auto;border-color:' + options.borderColor + ';border-style:' + options.borderStyle + ';border-width:' + options.borderWidth + 'px; height:80px; line-height:70px; padding-left:30px; padding-right: 10px;border-radius:18px; background: ' + options.backgroundColor + ' url(/static/img/loading-upload.gif) no-repeat 10px center; color:' + options.TipsColor + ';font-size:20px;">' + options.loadingTips + '</div></div>';
    $("body").append(_LoadingHtml);
    var _LoadingTipsH = document.getElementById("loadingTips").clientHeight;
    var _LoadingTipsW = document.getElementById("loadingTips").clientWidth;
    var _LoadingTop = _PageHeight > _LoadingTipsH ? (_PageHeight - _LoadingTipsH) / 2 : 0;
    var _LoadingLeft = _PageWidth > _LoadingTipsW ? (_PageWidth - _LoadingTipsW) / 2 : 0;
    $("#loadingTips").css({
      "left": _LoadingLeft + "px",
      "top": _LoadingTop + "px"
    });
    document.onreadystatechange = PageLoaded;
    function PageLoaded() {
      if (document.readyState == "complete") {
        var loadingMask = $('#loadingPage');
        setTimeout(function () {
          loadingMask.animate({
            "opacity": 0
          },
          options.delayTime,
          function () {
            $(this).hide();
          });
        },
        options.sleep);
      }
    }
  },
  end: function () {
    $("#loadingPage").remove();
  }
};


var _LoadingHtml =
    '<div id="loadingPage" style="' +
    'position:fixed;left:0;top:0;_position: absolute;width:100%;height:' + _PageHeight + 'px;background:' + options.backgroundColor + ';opacity:' + options.opacity + ';filter:alpha(opacity=' + options.opacity * 100 + ');z-index:' + options.zindex + ';"><div id="loadingTips" style="position: absolute; cursor1: wait; width: auto;border-color:' + options.borderColor + ';border-style:' + options.borderStyle + ';border-width:' + options.borderWidth + 'px; height:80px; line-height:70px; padding-left:30px; padding-right: 10px;border-radius:18px; background: ' + options.backgroundColor + ' url(/static/img/loading-upload.gif) no-repeat 10px center; color:' + options.TipsColor + ';font-size:20px;">' + options.loadingTips + '</div></div>';
