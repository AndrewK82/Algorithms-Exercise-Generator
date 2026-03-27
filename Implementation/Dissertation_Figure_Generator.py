import random
import math
import os
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker
import numpy as np

# ------------------------------------------------------------------
# CONFIGURATION 
# ------------------------------------------------------------------

SYMBOLS = ['A', 'C', 'G', 'T']

SCALING_FACTORS = {
    'low_entropy': 0.4,
    'high_entropy': 0.7
}

STEP_FACTORS = {
    'high_entropy': 0.65,
    'low_entropy':  0.65
}

TOLERANCES = {
    'high_entropy': 1,
    'low_entropy':  3
}

# ------------------------------------------------------------------
# Core LZW functions
# ------------------------------------------------------------------

def calculate_shannon_entropy(text):
    counts = Counter(text)
    length = len(text)
    entropy = 0.0
    for count in counts.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy


def calculate_visual_variance(text):
    bigrams = set(text[i] + text[i+1] for i in range(len(text) - 1))
    return len(bigrams) / (len(SYMBOLS) ** 2)


def calculate_target_dict_size(length, entropy_type):
    base_size = len(SYMBOLS)
    growth = int(length * SCALING_FACTORS[entropy_type])
    return base_size + max(3, growth)


def calculate_target_steps(length, entropy_type):
    return max(4, int(length * STEP_FACTORS[entropy_type]))


def simulate_lzw(text):
    dictionary = {ch: idx for idx, ch in enumerate(SYMBOLS)}
    dict_size = len(dictionary)
    w = ""
    output = []
    matches = []
    for c in text:
        wc = w + c
        if wc in dictionary:
            w = wc
        else:
            if w:
                output.append(dictionary[w])
                matches.append(w)
            dictionary[wc] = dict_size
            dict_size += 1
            w = c
    if w:
        output.append(dictionary[w])
        matches.append(w)
    return dict_size, output, matches


def generate_smart_lzw_string(length, entropy_type, track_attempts=False):
    target_dict_size = calculate_target_dict_size(length, entropy_type)
    target_steps     = calculate_target_steps(length, entropy_type)
    base_tolerance   = TOLERANCES[entropy_type]
    max_streak       = 2 if entropy_type == 'high_entropy' else 3

    if entropy_type == 'high_entropy':
        weights = [0.25, 0.25, 0.25, 0.25]
    else:
        weights = [0.65, 0.18, 0.10, 0.07]

    for attempt in range(1, 100001):
        current_tolerance = base_tolerance + (attempt // 25000)

        text_list = random.sample(SYMBOLS, len(SYMBOLS))
        text_list += random.choices(SYMBOLS, weights=weights, k=length - 4)
        random.shuffle(text_list)
        text = "".join(text_list)

        has_streak = any(
            text[i:i+max_streak+1] == text[i] * (max_streak+1)
            for i in range(len(text) - max_streak)
        )
        if has_streak:
            continue

        d_size, compressed, _ = simulate_lzw(text)
        steps = len(compressed)

        if (abs(d_size - target_dict_size) <= current_tolerance
                and abs(steps - target_steps) <= current_tolerance
                and len(compressed) < len(text)):
            
            entropy_value = calculate_shannon_entropy(text)
            if track_attempts:
                return text, d_size, compressed, entropy_value, attempt
            return text, d_size, compressed, entropy_value

    if track_attempts:
        return text, d_size, compressed, calculate_shannon_entropy(text), 100000
    raise ValueError(f"Failed to generate valid sequence for length {length}")


# ------------------------------------------------------------------
# Plot styling
# ------------------------------------------------------------------

HIGH_COL  = '#2166AC'
LOW_COL   = '#D6604D'
HIGH_FILL = '#AEC7E8'
LOW_FILL  = '#F4A582'

plt.rcParams.update({
    'font.family':     'serif',
    'font.size':       11,
    'axes.titlesize':  12,
    'axes.labelsize':  11,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.dpi':      150,
    'savefig.dpi':     300,
    'savefig.bbox':    'tight',
})

OUT_DIR = "Figures"
os.makedirs(OUT_DIR, exist_ok=True)

LENGTHS = [8, 10, 12, 14, 16, 18, 20, 22, 25, 28, 30]
N_REPS  = 15


# ------------------------------------------------------------------
# Data collection
# ------------------------------------------------------------------

def collect_scaling_data():
    data  = {p: {l: [] for l in LENGTHS} for p in ('high_entropy', 'low_entropy')}
    total = len(LENGTHS) * 2 * N_REPS
    done  = 0

    for profile in ('high_entropy', 'low_entropy'):
        for length in LENGTHS:
            for _ in range(N_REPS):
                text, d_size, compressed, entropy = generate_smart_lzw_string(
                    length, profile
                )
                iv    = calculate_visual_variance(text)
                steps = len(compressed)
                total_bits = sum(
                    max(2, math.ceil(math.log2(len(SYMBOLS) + i)))
                    for i in range(steps)
                )
                ratio = total_bits / (length * 8)

                data[profile][length].append({
                    'steps':   steps,
                    'entropy': entropy,
                    'd_size':  d_size,
                    'ratio':   ratio,
                    'iv':      iv,
                })
                done += 1
            print(f"  {done}/{total}  length={length} profile={profile}")

    return data


# ------------------------------------------------------------------
# Helper
# ------------------------------------------------------------------

def extract(data, profile, key):
    means = [np.mean([r[key] for r in data[profile][l]]) for l in LENGTHS]
    stds  = [np.std( [r[key] for r in data[profile][l]]) for l in LENGTHS]
    return np.array(means), np.array(stds)


def plot_with_band(ax, x, means, stds, color, fill, label):
    ax.plot(x, means, 'o-', color=color, linewidth=2, markersize=5, label=label)
    ax.fill_between(x, means - stds, means + stds, color=fill, alpha=0.35)


# ------------------------------------------------------------------
# Figure 1 — Step count vs string length
# ------------------------------------------------------------------

def fig_steps_vs_length(data):
    fig, ax = plt.subplots(figsize=(6.5, 4))
    x = np.array(LENGTHS)

    for profile, col, fill, lbl in [
        ('high_entropy', HIGH_COL, HIGH_FILL, 'High entropy profile'),
        ('low_entropy',  LOW_COL,  LOW_FILL,  'Low entropy profile'),
    ]:
        means, stds = extract(data, profile, 'steps')
        plot_with_band(ax, x, means, stds, col, fill, lbl)

    targets = [calculate_target_steps(l, 'high_entropy') for l in LENGTHS]
    ax.plot(x, targets, 'k--', linewidth=1.4, label='Target ($0.65n$)', zorder=5)

    ax.set_xlabel('String length $n$')
    ax.set_ylabel('Number of output steps')
    ax.set_title('Step count scales linearly with string length')
    ax.legend(framealpha=0.9)
    ax.grid(alpha=0.25)
    path = os.path.join(OUT_DIR, 'fig1_steps_vs_length.pdf')
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")


# ------------------------------------------------------------------
# Figure 2 — Entropy vs string length
# ------------------------------------------------------------------

def fig_entropy_vs_length(data):
    fig, ax = plt.subplots(figsize=(6.5, 4))
    x = np.array(LENGTHS)

    for profile, col, fill, lbl in [
        ('high_entropy', HIGH_COL, HIGH_FILL, 'High entropy profile'),
        ('low_entropy',  LOW_COL,  LOW_FILL,  'Low entropy profile'),
    ]:
        means, stds = extract(data, profile, 'entropy')
        plot_with_band(ax, x, means, stds, col, fill, lbl)

    ax.axhline(2.0, color='grey', linestyle=':', linewidth=1.2,
               label='Maximum entropy ($\\log_2 4 = 2$ bits)')
    ax.set_xlabel('String length $n$')
    ax.set_ylabel('Shannon entropy (bits per symbol)')
    ax.set_title('Entropy by profile stabilises quickly with string length')
    ax.set_ylim(0.8, 2.15)
    ax.legend(framealpha=0.9)
    ax.grid(alpha=0.25)
    path = os.path.join(OUT_DIR, 'fig2_entropy_vs_length.pdf')
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")


# ------------------------------------------------------------------
# Figure 3 — Dictionary size vs string length
# ------------------------------------------------------------------

def fig_dictsize_vs_length(data):
    fig, ax = plt.subplots(figsize=(6.5, 4))
    x = np.array(LENGTHS)

    for profile, col, fill, lbl in [
        ('high_entropy', HIGH_COL, HIGH_FILL, 'High entropy profile'),
        ('low_entropy',  LOW_COL,  LOW_FILL,  'Low entropy profile'),
    ]:
        means, stds = extract(data, profile, 'd_size')
        plot_with_band(ax, x, means, stds, col, fill, lbl)

        targets = [calculate_target_dict_size(l, profile) for l in LENGTHS]
        ax.plot(x, targets, linestyle='--', color=col, linewidth=1, alpha=0.6)

    ax.set_xlabel('String length $n$')
    ax.set_ylabel('Final dictionary size (entries)')
    ax.set_title('Dictionary growth scales with length; high entropy grows faster')
    ax.legend(framealpha=0.9)
    ax.grid(alpha=0.25)
    ax.annotate('Dashed = target', xy=(0.97, 0.08),
                xycoords='axes fraction', ha='right', fontsize=9, color='grey')

    path = os.path.join(OUT_DIR, 'fig3_dictsize_vs_length.pdf')
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")


# ------------------------------------------------------------------
# Figure 4 — Compression ratio vs string length
# ------------------------------------------------------------------

def fig_ratio_vs_length(data):
    fig, ax = plt.subplots(figsize=(6.5, 4))
    x = np.array(LENGTHS)

    for profile, col, fill, lbl in [
        ('high_entropy', HIGH_COL, HIGH_FILL, 'High entropy profile'),
        ('low_entropy',  LOW_COL,  LOW_FILL,  'Low entropy profile'),
    ]:
        means, stds = extract(data, profile, 'ratio')
        plot_with_band(ax, x, means, stds, col, fill, lbl)

    ax.axhline(1.0, color='black', linestyle=':', linewidth=1.2,
               label='No compression (ratio = 1)')
    ax.set_xlabel('String length $n$')
    ax.set_ylabel('Compression ratio (compressed / original bits)')
    ax.set_title('Compression ratio improves with length; low entropy compresses better')
    ax.legend(framealpha=0.9)
    ax.grid(alpha=0.25)
    path = os.path.join(OUT_DIR, 'fig4_ratio_vs_length.pdf')
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")


# ------------------------------------------------------------------
# Figure 5 — Entropy vs input variance scatter
# ------------------------------------------------------------------

def fig_entropy_vs_iv(data):
    fig, ax = plt.subplots(figsize=(6.5, 4.5))

    for profile, col, edge, lbl in [
        ('high_entropy', HIGH_COL, '#1A4F8A', 'High entropy profile'),
        ('low_entropy',  LOW_COL,  '#B03A2E', 'Low entropy profile'),
    ]:
        xs, ys = [], []
        for length in LENGTHS:
            for r in data[profile][length]:
                xs.append(r['entropy'])
                ys.append(r['iv'])
        ax.scatter(xs, ys, c=col, edgecolors=edge, linewidths=0.4,
                   alpha=0.65, s=30, label=lbl, zorder=3)

    ax.set_xlabel('Shannon entropy (bits per symbol)')
    ax.set_ylabel('Input Variance $V(s)$')
    ax.set_title('Entropy and input variance are related but not identical')
    ax.legend(framealpha=0.9, loc='upper left', bbox_to_anchor=(0.0, 0.75))
    ax.grid(alpha=0.25)

    ax.text(0.97, 0.03,
            'Points spread along both axes show that\n'
            'entropy alone does not determine input variance',
            transform=ax.transAxes, fontsize=9, va='bottom', ha='right',
            bbox=dict(boxstyle='round,pad=0.3', fc='lightyellow',
                      ec='goldenrod', alpha=0.9))

    path = os.path.join(OUT_DIR, 'fig5_entropy_vs_iv.pdf')
    fig.savefig(path)
    plt.close(fig)
    print(f"  Saved: {path}")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

def main():
    print(f"\nCollecting scaling data ({len(LENGTHS)} lengths x 2 profiles x {N_REPS} reps)...\n")
    data = collect_scaling_data()

    print("\nPlotting figures...")
    fig_steps_vs_length(data)
    fig_entropy_vs_length(data)
    fig_dictsize_vs_length(data)
    fig_ratio_vs_length(data)
    fig_entropy_vs_iv(data)

    print(f"\nAll figures saved to ./{OUT_DIR}/")
    print("\nSummary table (mean +/- std at n=16):")
    print(f"{'Metric':<20} {'High entropy':>20} {'Low entropy':>20}")

    idx = LENGTHS.index(16)

    for key, label in [('steps', 'Steps'), ('entropy', 'Entropy'),
                       ('d_size', 'Dict size'), ('ratio', 'Comp ratio')]:
        hm, hs = extract(data, 'high_entropy', key)
        lm, ls = extract(data, 'low_entropy',  key)
        print(f"{label:<20} {hm[idx]:>10.3f} +/- {hs[idx]:<8.3f} "
              f"{lm[idx]:>10.3f} +/- {ls[idx]:<8.3f}")


if __name__ == "__main__":
    main()