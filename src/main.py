import curses
import sys

import numpy as np
import matplotlib.pyplot as plt
import npyscreen
import codecs


class GraphDrawer(npyscreen.NPSAppManaged):
    data = ([], [], 0)

    def onStart(self):
        self.addForm("MAIN", File)
        self.addForm("PLOT_CONFIG", Selector)


class File(npyscreen.ActionForm):

    def on_ok(self):
        self.parentApp.data = read_file(self.file_name.value)
        if self.selector_action.value[0] == 0:
            self.parentApp.setNextForm("PLOT_CONFIG")
        else:
            export(self.parentApp.data, self.file_name.value)
            self.parentApp.setNextForm(None)

    def on_cancel(self):
        self.parentApp.setNextForm(None)

    def create(self):
        self.file_name = self.add(npyscreen.TitleFilenameCombo, name="Filename:")
        self.selector_action = self.add(npyscreen.TitleSelectOne, max_height=2, value=[0], name="Action:",
                                        values=["Plot data", "Export data (csv)"], scroll_exit=True)


class Selector(npyscreen.ActionForm):

    def beforeEditing(self):

        self.title = self.add(npyscreen.TitleText, name="Title:", max_height=3)
        self.add(npyscreen.FixedText, value="---------------- X axis ----------------", labelColor="NO_EDIT")
        self.selector_x = self.add(npyscreen.TitleSelectOne, max_height=2, value=[0], name="X axis",
                                   values=self.parentApp.data[0], scroll_exit=True)
        self.x_unit = self.add(npyscreen.TitleText, name="X unit:")
        self.x_min = self.add(npyscreen.TitleText, name="X min:")
        self.x_max = self.add(npyscreen.TitleText, name="X max:")
        self.add(npyscreen.FixedText, value="---------------- Y axis ----------------", labelColor="NO_EDIT")
        self.selector_y = self.add(npyscreen.TitleMultiSelect, max_height=12, value=[1], name="Y axis",
                                   values=self.parentApp.data[0], scroll_exit=True)
        self.y_unit = self.add(npyscreen.TitleText, name="Y unit:")
        self.y_min = self.add(npyscreen.TitleText, name="Y min:")
        self.y_max = self.add(npyscreen.TitleText, name="Y max:")

        self.add(npyscreen.FixedText, value="---------------- Time settings ----------------", labelColor="NO_EDIT")
        self.t_min = self.add(npyscreen.TitleText, name="t min:")
        self.t_max = self.add(npyscreen.TitleText, name="t max:")

        self.add(npyscreen.FixedText, value="---------------- data settings ----------------", labelColor="NO_EDIT")

        if self.parentApp.data[2] > 1:
            self.mes_id = self.add(npyscreen.TitleText,
                                   name="Measurement id (0 to " + str(self.parentApp.data[2] - 1) + ")")
        else:
            self.mes_id = None

        self.add(npyscreen.FixedText, value="", labelColor="NO_EDIT")

        self.black = self.add(npyscreen.TitleText, name="Black and white plot ? (Y/N)")

    def on_ok(self):

        if self.black.value.upper() == "Y":
            plt.style.use('grayscale')
        else:
            plt.style.use('bmh')

        plt.title(self.title.value)

        id = 0
        if self.mes_id is not None:
            try:
                id = int(self.mes_id.value)
            except:
                pass

        x_index = int(self.selector_x.value[0])
        y_index = [int(x) for x in self.selector_y.value]

        try:
            v_min = int((500.0 * int(self.t_min.value)) / 10.0)
        except:
            v_min = 0

        try:
            v_max = int((500.0 * int(self.t_max.value)) / 10.0)
        except:
            v_max = 500

        if x_index == 0:
            x_plot = np.linspace(0, 10, 500)
        else:
            x_plot = [val[x_index - 1] for val in self.parentApp.data[1][id]]
            x_plot = x_plot[v_min:v_max]

        for y in y_index:
            if y == 0:
                y_plot = np.linspace(0, 10, 500)
            else:
                y_plot = [val[y - 1] for val in self.parentApp.data[1][id]]
                y_plot = y_plot[v_min:v_max]

            plt.plot(x_plot, y_plot, label=self.parentApp.data[0][y])

        if len(y_index) == 1:
            label = self.parentApp.data[0][y_index[0]]
            if not self.y_unit == "":
                label += " (" + self.y_unit.value + ")"
            plt.ylabel(label)
        else:
            plt.legend()

        label = self.parentApp.data[0][x_index]
        if not self.x_unit == "":
            label += " (" + self.x_unit.value + ")"
        plt.xlabel(label)

        try:
            plt.xlim(left=int(self.x_min.value))
        except:
            pass

        try:
            plt.xlim(right=int(self.x_max.value))
        except:
            pass

        try:
            plt.ylim(bottom=int(self.y_min.value))
        except:
            pass

        try:
            plt.xlim(top=int(self.y_max.value))
        except:
            pass

        plt.axis('tight')
        plt.grid(True)
        plt.savefig("tst.png", dpi=600)

        self.parentApp.setNextForm(None)

    def on_cancel(self):
        self.parentApp.setNextForm(None)


def export(data, name):
    with open(name + ".csv", "w") as f:
        f.write("# Converted data file from " + data[3] + " with GraphDrawer, https://azuxul.fr \n")
        t = np.linspace(0, 10, 500)
        for i in range(data[2]):
            f.write("\n")
            f.write("Measurement id: " + str(i) + "\n")
            f.write(";".join(data[0]) + "\n")
            for j in range(len(data[1][i])):
                f.write(str(t[j]) + ";" + ";".join([str(x) for x in data[1][i][j]]) + "\n")

        f.write("")


def read_file(name):
    legend = []
    data = []
    nb = -1
    device_name = ""

    with codecs.open(name, "r", "iso-8859-1") as f:
        device_name = f.readline().rstrip()
        f.readline()
        mes_nb = f.readline().split("    ")
        nb = int(mes_nb[0])
        legend_line = f.readline()
        legend = legend_line.split("I")
        legend.pop(0)
        legend.pop(-1)
        for index in range(len(legend)):
            for i in range(len(legend[index]) - 1):
                if legend[index][i] is ' ' and legend[index][i + 1] is ' ':
                    legend[index] = legend[index][:i]
                    break

        legend.insert(0, "Time")
        buf = []
        for l in f:
            if l == legend_line:
                data.append(buf)
                buf = []
            else:
                raw_data = l.split(" ")
                for e in raw_data:
                    if len(e) < 1:
                        raw_data.remove(e)
                    else:
                        e.replace(" ", "")

                raw_data.pop(-1)
                buf.append([float(e) for e in raw_data])

        data.append(buf)

    return legend, data, nb, device_name


if __name__ == "__main__":
    GraphDrawer().run()
