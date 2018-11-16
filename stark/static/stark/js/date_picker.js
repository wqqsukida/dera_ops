(function ($) {
    $('.date-picker').datetimepicker({
        minView: "month",
        language: "zh-CN",
        sideBySide: true,
        format: 'yyyy-mm-dd',
        bootcssVer: 3,
        startDate: new Date(),
        autoclose: true
    })

})(jQuery);