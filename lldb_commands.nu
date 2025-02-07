def sections [exe -d -k ] {
    mut sections_cmd = "sections -c"
    if $d {
        $sections_cmd = $sections_cmd + " -d"
    }
    if $k {
        $sections_cmd = $sections_cmd + " -k"
    }
    
    lldb -Q -b -o $sections_cmd $exe
    | tail -n +2
    | from csv
    #| update cells -c [start, end, size] { |$value| ($value | into int| format number | get upperhex )}
}