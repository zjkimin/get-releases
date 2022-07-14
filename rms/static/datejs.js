function diff_date(old_date) {
    var odate = new Date(old_date);
    var now_date = new Date();
    sec_diff = now_date - odate
    if (sec_diff <= 60) {
        return '一分钟内'
    }
    date_diff = new Date(sec_diff);
    year_diff = date_diff.getUTCFullYear() > 1970 ? date_diff.getUTCFullYear() - 1970 + '年' : '';
    month_diff = date_diff.getUTCMonth() > 0 ? date_diff.getUTCMonth() + '月' : '';
    day_diff = date_diff.getUTCDate() > 1 ? date_diff.getUTCDate() - 1 + '天' : '';
    hours_diff = date_diff.getUTCHours() + '时';
    minute_diff = date_diff.getUTCMinutes() + '分';
    sec_diff = date_diff.getUTCSeconds() + '秒';
    ret = year_diff + month_diff + day_diff;
    if (year_diff != '') {
        return odate.toLocaleDateString() + ' ' + ret + '前';
    }
    return ret + hours_diff + minute_diff + sec_diff + '前';
}
