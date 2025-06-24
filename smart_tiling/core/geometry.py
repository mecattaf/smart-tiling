"""
Core geometry-based tiling logic (preserved from original autotiling).
This module maintains backward compatibility with the original autotiling behavior.
"""
import sys


def output_name(con):
    """Get the output name for a container by traversing up the tree."""
    if con.type == "root":
        return None

    if p := con.parent:
        if p.type == "output":
            return p.name
        else:
            return output_name(p)


def switch_splitting(i3, e, debug, outputs, workspaces, depth_limit, splitwidth, splitheight, splitratio):
    """
    Original autotiling logic for geometry-based window splitting.
    Preserved from the original implementation to maintain backward compatibility.
    """
    try:
        con = i3.get_tree().find_focused()
        output = output_name(con)
        # Stop, if outputs is set and current output is not in the selection
        if outputs and output not in outputs:
            if debug:
                print(f"Debug: Autotiling turned off on output {output}", file=sys.stderr)
            return

        if con and not workspaces or (str(con.workspace().num) in workspaces):
            if con.floating:
                # We're on i3: on sway it would be None
                # May be 'auto_on' or 'user_on'
                is_floating = "_on" in con.floating
            else:
                # We are on sway
                is_floating = con.type == "floating_con"

            if depth_limit:
                # Assume we reached the depth limit, unless we can find a workspace
                depth_limit_reached = True
                current_con = con
                current_depth = 0
                while current_depth < depth_limit:
                    # Check if we found the workspace of the current container
                    if current_con.type == "workspace":
                        # Found the workspace within the depth limitation
                        depth_limit_reached = False
                        break

                    # Look at the parent for next iteration
                    current_con = current_con.parent

                    # Only count up the depth, if the container has more than
                    # one container as child
                    if len(current_con.nodes) > 1:
                        current_depth += 1

                if depth_limit_reached:
                    if debug:
                        print("Debug: Depth limit reached")
                    return

            is_full_screen = con.fullscreen_mode == 1
            is_stacked = con.parent.layout == "stacked"
            is_tabbed = con.parent.layout == "tabbed"

            # Exclude floating containers, stacked layouts, tabbed layouts and full screen mode
            if (not is_floating
                    and not is_stacked
                    and not is_tabbed
                    and not is_full_screen):
                new_layout = "splitv" if con.rect.height > con.rect.width / splitratio else "splith"

                if new_layout != con.parent.layout:
                    result = i3.command(new_layout)
                    if result[0].success and debug:
                        print(f"Debug: Switched to {new_layout}", file=sys.stderr)
                    elif debug:
                        print(f"Error: Switch failed with err {result[0].error}", file=sys.stderr)

                if e.change in ["new", "move"] and con.percent:
                    if con.parent.layout == "splitv" and splitheight != 1.0:  # top / bottom
                        # print(f"split top fac {splitheight*100}")
                        i3.command(f"resize set height {int(con.percent * splitheight * 100)} ppt")
                    elif con.parent.layout == "splith" and splitwidth != 1.0:  # top / bottom:                     # left / right
                        # print(f"split right fac {splitwidth*100} ")
                        i3.command(f"resize set width {int(con.percent * splitwidth * 100)} ppt")

        elif debug:
            print("Debug: No focused container found or autotiling on the workspace turned off", file=sys.stderr)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)