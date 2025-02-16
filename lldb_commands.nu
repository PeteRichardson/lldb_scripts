def sections [exe --decimal(-d) --all(-a) --skip-subsections(-s) --csv(-c)] {
    # have the lldb command actually spit out csv, which is easier to 
    # convert into a nushell table (had one case where space-separated columns
    # didn't actually line up right, so from csv got confused)
    mut sections_cmd = "sections -c"

    if $decimal {
        $sections_cmd = $sections_cmd + " -d"      # display numbers in decimal
    }    
    if $all {
        $sections_cmd = $sections_cmd + " -a"      # include all dependencies
    }
    if $skip_subsections {
        $sections_cmd = $sections_cmd + " -s"      # skip subsections
    }

    # Call lldb to do the work (assumes section.py module is loaded in lldb)
    mut output = lldb -Q -b -o $sections_cmd $exe | lines

    # Should check for errors here... what if exe is corrupt?
    if ($output | is-empty) {
        echo "No sections found in $exe.  Confirm the file exists and is a valid executable."
        return []
    }

    # remove the "Current executable set to..." line which target create emits
    if ($output.0 | str starts-with "Current") {
        $output = ($output | skip 1)
    }

    # re-encode into csv text if user actually specified -c
    # otherwise, make it into a nushell table
    # with numeric columns for start, end, size (but only if values are int, not hex :-(
    # nushell doesn't seem to think hex numbers are numbers.)
    mut $csv_output = ($output | to text)
    if ($csv) {
        $csv_output
    } else {
        # convert to nushell table.   Make size column into type filesize
        mut $output = ($csv_output | from csv | update cells -c [size] { |$value| ($value | into int| into filesize )})

        if $decimal {
           $output = $output | update cells -c [start, end] { |$value| ($value | into int )}
        } 
        $output
    }
}

def lf [exe func --snip(-s)] {
    let lldb_cmd = "lf " + $func
    lldb -b -o $lldb_cmd $exe | tail -n +7 | bat -l c
}
# TODO: re-implement nushell lf command just parse the filename and line numbers
# from the lldb output and then use bat to display that portion of the file.
# e.g. bat -r 25:50 /Users/pete/practice/c/pth/main.c
#
# Benefits:
# 1. bat can handle the syntax highlighting, line numbers, file name
# 4. won't need to tail -n +7 or specify -l c
# 5. bat can handle the file not found | not readable | not a text file, etc


# Doesn't work yet!
def "format hex" [columns: list<string>] {
    each {|row|
        let updated_row = $row
        for col in $columns {
            if ($row | get $col | is-not-empty) {
                let updated_row = ($updated_row | update $col {|s| (get $s | format number | get upperhex)})
            }
        }
        $updated_row
    }
}

def "format sections" [] {
    format hex [start end size]
}