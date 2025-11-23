import matplotlib.pyplot as plt
import matplotlib.patches as patches

TOTAL_LENGTH = 1250
MID_X = TOTAL_LENGTH / 2

def draw_dim_line(ax, start_x, end_x, y_pos, text, color='black', arrow_style='<->', text_offset=5, ref_y=0):
    ax.annotate('', xy=(start_x, y_pos), xytext=(end_x, y_pos),
        arrowprops=dict(arrowstyle=arrow_style, color=color, lw=1.2))
    mid_point = (start_x + end_x) / 2
    ax.text(mid_point, y_pos + text_offset, text, ha='center', va='bottom', 
        color=color, fontsize=10, fontweight='bold', 
        bbox=dict(facecolor='white', edgecolor='none', pad=1))
    
    y_obj = ref_y
    ax.plot([start_x, start_x], [y_obj, y_pos], color=color, linestyle=':', lw=0.8, alpha=0.5)
    ax.plot([end_x, end_x], [y_obj, y_pos], color=color, linestyle=':', lw=0.8, alpha=0.5)

def add_callout(ax, x, y, text, xytext, color='black'):
    ax.annotate(text, xy=(x, y), xytext=xytext,
        arrowprops=dict(arrowstyle='->', color=color, lw=1.5),
        fontsize=11, fontweight='bold', color=color, ha='center', va='center',
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=color, alpha=1.0))

def draw_top_view():
    fig, ax = plt.subplots(figsize=(18, 7))
    
    deck_width = 100 
    diaph_locs = [20, 30, 425, 825, 1220, 1230]
    top_split_locs = [234, 1016]
    dim_top = [(234, "234"), (782, "782"), (234, "234")]

    ax.set_title("Top View (Deck Width = 100mm)", fontsize=16, pad=20, fontweight='bold', loc='left')
    
    ax.add_patch(patches.Rectangle((0, 0), TOTAL_LENGTH, deck_width, facecolor='#e6f2ff', edgecolor='#00509d', lw=2))
    
    ax.axvline(x=MID_X, color='#0066cc', linestyle='-.', alpha=0.5)
    ax.text(MID_X, -15, "CL", color='#0066cc', ha='center', fontweight='bold')
    
    for i, x in enumerate(diaph_locs):
        ax.plot([x, x], [0, deck_width], color='#d62728', linestyle='--', alpha=0.7, lw=1.5)
        if i == 2: 
            add_callout(ax, x, deck_width/2, "Int. Diaphragm", (x-80, deck_width/2 + 30), color='#d62728')

    for x in top_split_locs:
        ax.plot([x, x], [0, deck_width], color='#00509d', lw=3)
    add_callout(ax, top_split_locs[0], 10, "Top Split Line", (top_split_locs[0]+80, -25), color='#00509d')

    curr_x = 0
    y_dim = deck_width + 40
    ax.text(-80, y_dim, "Top Layer\nDivisions", va='bottom', ha='right', color='#00509d', fontweight='bold')
    for length, label in dim_top:
        draw_dim_line(ax, curr_x, curr_x + length, y_dim, label, color='#00509d', ref_y=deck_width)
        curr_x += length
        
    ax.annotate('', xy=(-30, 0), xytext=(-30, deck_width), arrowprops=dict(arrowstyle='<|-|>', color='black'))
    ax.text(-45, deck_width/2, "100", rotation=90, ha='center', va='center', fontweight='bold')

    ax.set_ylim(-40, deck_width + 60)
    ax.set_xlim(-150, TOTAL_LENGTH + 150)
    ax.set_aspect('equal')
    ax.axis('off')
    
    ax.legend(handles=[plt.Line2D([0], [0], color='#d62728', linestyle='--', label='Internal Diaphragm'), plt.Line2D([0], [0], color='#00509d', lw=3, label='Top Split Line')],
        loc='upper right', 
        bbox_to_anchor=(1.0, 1.6), # Increased from 1.3 to 1.6
        framealpha=1)


def draw_bottom_view():
    fig, ax = plt.subplots(figsize=(20, 10))
    
    deck_width = 100    
    shell_width = 80    
    
    shell_split_locs = [312.5, 937.5]
    splice_width = 50
    dim_shell = [(312.5, "312.5"), (625, "625"), (312.5, "312.5")]

    ax.set_title("Bottom View (Looking Up)", fontsize=18, pad=40, fontweight='bold', loc='left')
    
    zone_y = deck_width + 40
    ax.text(62.5, zone_y, "Support Zone", ha='center', va='bottom', fontsize=10, color='#777')
    ax.text(317.5, zone_y, "Transition Zone", ha='center', va='bottom', fontsize=10, color='#777')
    ax.text(MID_X, zone_y, "Central Zone", ha='center', va='bottom', fontsize=10, color='#777')
    ax.text(967.5, zone_y, "Transition Zone", ha='center', va='bottom', fontsize=10, color='#777')
    ax.text(1187.5, zone_y, "Support Zone", ha='center', va='bottom', fontsize=10, color='#777')
    
    for zx in [125, 510, 810, 1125]:
        ax.axvline(x=zx, ymin=0, ymax=0.90, color='#ccc', linestyle='--', linewidth=1, zorder=0)

    ax.add_patch(patches.Rectangle((0, 0), TOTAL_LENGTH, deck_width, facecolor='#f0f8ff', edgecolor='#00509d', lw=1, zorder=1, label='Deck Overhang (100mm)'))
    
    y_shell_offset = (deck_width - shell_width) / 2
    ax.add_patch(patches.Rectangle((0, y_shell_offset), TOTAL_LENGTH, shell_width, facecolor='#fff5fd', edgecolor='#663399', lw=2.5, zorder=2, label='Shell Bottom (80mm)'))

    ax.axvline(x=MID_X, color='#0066cc', linestyle='-.', alpha=0.6, zorder=3)

    for x in shell_split_locs:
        ax.plot([x, x], [y_shell_offset, y_shell_offset + shell_width], color='#800080', lw=1, linestyle='-', zorder=3)

    for center in shell_split_locs:
        s_start = center - (splice_width/2)
        ax.add_patch(patches.Rectangle((s_start, y_shell_offset), splice_width, shell_width, facecolor='none', edgecolor='black', hatch='////', lw=2, zorder=4))
        

    y_dim_shell = -30
    curr_x = 0
    ax.text(-80, y_dim_shell, "Shell Split\nLocations", va='bottom', ha='right', color='#800080', fontweight='bold')
    for length, label in dim_shell:
        draw_dim_line(ax, curr_x, curr_x + length, y_dim_shell, label, color='#800080', ref_y=y_shell_offset)
        curr_x += length

    x_dim_shell = TOTAL_LENGTH + 30
    ax.annotate('', xy=(x_dim_shell, y_shell_offset), xytext=(x_dim_shell, y_shell_offset+shell_width), arrowprops=dict(arrowstyle='<|-|>', color='#663399'))
    ax.text(x_dim_shell + 15, deck_width/2, "80", rotation=90, ha='center', va='center', fontweight='bold', color='#663399')

    x_dim_deck = -30
    ax.annotate('', xy=(x_dim_deck, 0), xytext=(x_dim_deck, deck_width), arrowprops=dict(arrowstyle='<|-|>', color='#00509d'))
    ax.text(x_dim_deck - 15, deck_width/2, "100", rotation=90, ha='center', va='center', fontweight='bold', color='#00509d')

    ax.set_ylim(-80, deck_width + 60)
    ax.set_xlim(-150, TOTAL_LENGTH + 150)
    ax.set_aspect('equal')
    ax.axis('off')
    
    legend_elements = [
        patches.Patch(facecolor='#f0f8ff', edgecolor='#00509d', lw=1, label='Deck (100mm Width)'),
        patches.Patch(facecolor='#fff5fd', edgecolor='#663399', lw=2.5, label='Shell Bottom (80mm Width)'),
        patches.Patch(facecolor='none', hatch='////', edgecolor='black', label='Visible Splice Mend'),
    ]
    ax.legend(handles=legend_elements, 
              loc='upper right', 
              bbox_to_anchor=(1.0, 1.6), # Increased from 1.35 to 1.6
              framealpha=1)

if __name__ == "__main__":
    draw_bottom_view()
    draw_top_view()
    plt.show()