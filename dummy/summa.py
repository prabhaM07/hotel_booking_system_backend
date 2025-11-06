import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

# Apply Seaborn's built-in style
sns.set_theme(style="whitegrid")

# Generate some data
x = np.linspace(0, 10, 100)
df = pd.DataFrame({
    "x": x,
    "sin": np.sin(x),
    "cos": np.cos(x),
    "category": np.random.choice(["A", "B", "C"], size=100),
    "values": np.random.randint(1, 10, size=100)
})

# --- Report page with multiple plots ---
fig, axs = plt.subplots(2, 2, figsize=(10, 8))

# Sine plot
sns.lineplot(x="x", y="sin", data=df, ax=axs[0, 0], color="royalblue")
axs[0, 0].set_title("Sine Wave (Seaborn Line Plot)")

# Cosine plot
sns.lineplot(x="x", y="cos", data=df, ax=axs[0, 1], color="darkorange")
axs[0, 1].set_title("Cosine Wave (Seaborn Line Plot)")

# Bar chart
sns.barplot(x="category", y="values", data=df, ax=axs[1, 0], palette="mako")
axs[1, 0].set_title("Bar Chart (Seaborn)")

# Pie chart (still pure Matplotlib)
axs[1, 1].pie([10, 20, 30], labels=["Apples", "Bananas", "Cherries"], autopct="%1.1f%%", colors=sns.color_palette("pastel"))
axs[1, 1].set_title("Pie Chart (Matplotlib)")

plt.tight_layout()
plt.show()

# --- Save first report as PDF ---
fig.savefig("report.pdf")

# --- Multi-page PDF with dynamic plots ---
with PdfPages("full_report.pdf") as pdf:
    for i in range(3):
        fig, ax = plt.subplots()
        sns.lineplot(x=x, y=np.sin(x + i), ax=ax, color="teal")
        ax.set_title(f"Dynamic Plot {i+1}")
        pdf.savefig(fig)
        plt.close(fig)
