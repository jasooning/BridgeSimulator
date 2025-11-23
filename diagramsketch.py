import matplotlib.pyplot as plt
import matplotlib.patches as patches

def draw_bridge_diagram():
    fig, ax = plt.subplots(figsize=(18, 11))

    total_length = 1250
    beam_height = 100
    mid_x = total_length / 2  
    
    sections = [
        (0, 125, "Support", '#e0e0e0'),
        (125, 510, "Transition", '#f2f2f2'),
        (510, 810, "Central", '#ffffff'),
        (810, 1125, "Transition", '#f2f2f2'),
        (1125, 1250, "Support", '#e0e0e0')
    ]
    
    diaph_locs = [20, 30, 425, 825, 1220, 1230]
    
    splice_centers = [312.5, 937.5]
    splice_width = 50
    
    dim_top_layer = [(234, "234"), (782, "782"), (234, "234")]
    dim_core = [(125, "Shell Core\n125"), (1000, "No Core\n1000"), (125, "Shell Core\n125")]
    dim_shell = [(312.5, "312.5"), (625, "625"), (312.5, "312.5")]

    def draw_dim_line(start_x, end_x, y_pos, text, color='black', arrow_style='<->', text_offset=5, show_drops=True, font_size=10, font_weight='bold'):
        ax.annotate('', xy=(start_x, y_pos), xytext=(end_x, y_pos),
            arrowprops=dict(arrowstyle=arrow_style, color=color, lw=1.2))
        mid_point = (start_x + end_x) / 2
        ax.text(mid_point, y_pos + text_offset, text, ha='center', va='bottom', 
            color=color, fontsize=font_size, fontweight=font_weight, backgroundcolor='white')
        
        if show_drops:
            beam_edge_y = beam_height if y_pos > 0 else 0
            alpha = 0.3
            ax.plot([start_x, start_x], [beam_edge_y, y_pos], color=color, linestyle=':', lw=0.8, alpha=alpha)
            ax.plot([end_x, end_x], [beam_edge_y, y_pos], color=color, linestyle=':', lw=0.8, alpha=alpha)

    ax.axvline(x=mid_x, color='#0066cc', linestyle='-.', linewidth=1.2, alpha=0.6, zorder=0) #center line
    ax.text(mid_x, 290, "Center", ha='center', va='top', color='#0066cc', fontsize=12, fontweight='bold', bbox=dict(facecolor='white', edgecolor='none'))

    for start, end, label, color in sections:
        width = end - start
        rect = patches.Rectangle((start, 0), width, beam_height, linewidth=0, facecolor=color, zorder=1)
        ax.add_patch(rect)
        ax.text(start + width/2, beam_height/2, label, ha='center', va='center', 
            fontsize=11, color='black', alpha=0.15, fontweight='bold', zorder=2)

    for center in splice_centers:
        start_s = center - (splice_width / 2)
        rect = patches.Rectangle((start_s, 0), splice_width, beam_height, 
            linewidth=1, edgecolor='#444', facecolor='none', hatch='////', zorder=3)
        ax.add_patch(rect)
        ax.text(center, beam_height + 5, "Splice", rotation=90, ha='center', va='bottom', fontsize=8, color='#444')

    ax.add_patch(patches.Rectangle((0, 0), total_length, beam_height, linewidth=2, edgecolor='black', fill=False, zorder=4))

    for x in diaph_locs:
        ax.plot([x, x], [0, beam_height], color='#d62728', linewidth=2, linestyle='-', zorder=5)
        y_text = beam_height + 25 if x in [30, 1230] else beam_height + 10
        ax.text(x, y_text, str(x), color='#d62728', fontsize=8, rotation=90, ha='center', va='bottom', fontweight='bold')

    ax.plot(25, -5, marker='^', markersize=14, color='#ffcc00', markeredgecolor='black', clip_on=False, zorder=10)
    ax.plot(1225, -5, marker='o', markersize=14, color='#ffcc00', markeredgecolor='black', clip_on=False, zorder=10)
    
    y_25 = -45
    ax.annotate('', xy=(0, y_25), xytext=(25, y_25), arrowprops=dict(arrowstyle='<|-|>', color='#e6a800', lw=2))
    ax.text(12.5, y_25 + 5, "25", ha='center', va='bottom', color='#e6a800', fontsize=11, fontweight='bold')

    ax.annotate('', xy=(1225, y_25), xytext=(1250, y_25), arrowprops=dict(arrowstyle='<|-|>', color='#e6a800', lw=2))
    ax.text(1237.5, y_25 + 5, "25", ha='center', va='bottom', color='#e6a800', fontsize=11, fontweight='bold')
    
    ax.plot([0, 0], [0, y_25], color='#e6a800', linestyle=':', lw=1, alpha=0.5)
    ax.plot([1250, 1250], [0, y_25], color='#e6a800', linestyle=':', lw=1, alpha=0.5)


    y_top_1 = beam_height + 80
    ax.text(-80, y_top_1, "Top Layer", va='bottom', ha='right', fontsize=10, color='#00509d', fontweight='bold')
    curr_x = 0
    for length, label in dim_top_layer:
        draw_dim_line(curr_x, curr_x + length, y_top_1, label, color='#00509d')
        curr_x += length

    y_top_2 = beam_height + 130
    ax.text(-80, y_top_2, "Core", va='bottom', ha='right', fontsize=10, color='#2e8b57', fontweight='bold')
    curr_x = 0
    for length, label in dim_core:
        draw_dim_line(curr_x, curr_x + length, y_top_2, label, color='#2e8b57')
        curr_x += length

    y_base = -80 
    
    y_l1 = y_base
    l1_len = 1016
    l1_start = (total_length - l1_len) / 2
    l1_end = l1_start + l1_len
    
    ax.text(-80, y_l1, "Layer 1", va='bottom', ha='right', fontsize=10, color='black', fontweight='bold')
    ax.annotate('', xy=(l1_start, y_l1), xytext=(l1_end, y_l1), arrowprops=dict(arrowstyle='<->', color='black', lw=2.5))
    ax.text(mid_x, y_l1+5, "1016", ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.plot([l1_start, l1_start], [y_l1, 0], color='gray', linestyle=':', lw=0.5)
    ax.plot([l1_end, l1_end], [y_l1, 0], color='gray', linestyle=':', lw=0.5)

    ax.text(l1_start - 5, y_l1-2, f"{l1_start:.0f}", ha='right', va='top', fontsize=9, color='#444')

    y_l2 = y_base - 40
    l2_segments = [137.5, 625, 137.5]
    l2_current_x = (total_length - sum(l2_segments)) / 2
    
    ax.text(-80, y_l2, "Layer 2", va='center', ha='right', fontsize=10, color='black', fontweight='bold')
    
    for i, seg_len in enumerate(l2_segments):
        end_seg_x = l2_current_x + seg_len
        
        ax.annotate('', xy=(l2_current_x, y_l2), xytext=(end_seg_x, y_l2),
         arrowprops=dict(arrowstyle='<->', color='black', lw=2))
        ax.text((l2_current_x + end_seg_x)/2, y_l2+5, f"{seg_len}", ha='center', va='bottom', fontsize=10, fontweight='bold')
        ax.plot([l2_current_x, l2_current_x], [y_l2, 0], color='gray', linestyle=':', lw=0.5)
        ax.plot([end_seg_x, end_seg_x], [y_l2, 0], color='gray', linestyle=':', lw=0.5)
        
        l2_current_x += seg_len

    y_l3 = y_base - 80
    l3_start, l3_end = 510, 810
    ax.text(-80, y_l3, "Layer 3", va='bottom', ha='right', fontsize=10, color='black', fontweight='bold')
    ax.annotate('', xy=(l3_start, y_l3), xytext=(l3_end, y_l3), arrowprops=dict(arrowstyle='<->', color='black', lw=2))
    ax.text(mid_x, y_l3+5, "300", ha='center', va='bottom', fontsize=10, fontweight='bold')

    ax.text(l3_start, y_l3-5, "510", ha='center', va='top', fontsize=8, color='#444')
    ax.text(l3_end, y_l3-5, "810", ha='center', va='top', fontsize=8, color='#444')

    ax.plot([l3_start, l3_start], [y_l3, 0], color='gray', linestyle=':', lw=0.5)
    ax.plot([l3_end, l3_end], [y_l3, 0], color='gray', linestyle=':', lw=0.5)

    y_shell = y_base - 120
    ax.text(-80, y_shell, "Shell Split", va='bottom', ha='right', fontsize=10, color='#800080', fontweight='bold')
    curr_x = 0
    for length, label in dim_shell:
        draw_dim_line(curr_x, curr_x + length, y_shell, label, color='#800080', show_drops=False)
        curr_x += length

    ax.set_xlim(-120, total_length + 120)

    ax.set_ylim(-280, 320) 
    ax.set_aspect('equal')
    ax.axis('off')
    
    legend_patches = [
        patches.Patch(facecolor='#e0e0e0', edgecolor='none', label='Support/Shell Core'),
        patches.Patch(facecolor='#f2f2f2', edgecolor='none', label='Transition'),
        patches.Patch(facecolor='#ffffff', edgecolor='black', label='Central/No Core'),
        patches.Patch(facecolor='none', edgecolor='#444', hatch='////', label='Splice Mend'),
        plt.Line2D([0], [0], color='#0066cc', linestyle='-.', label='Centerline (CL)')
    ]
    ax.legend(handles=legend_patches, loc='upper right', bbox_to_anchor=(1.0, 1.05), ncol=3, fontsize=9)

    plt.title("Bridge Elevation View/Logitudinal Profile", fontsize=16, y=1.08)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    draw_bridge_diagram()