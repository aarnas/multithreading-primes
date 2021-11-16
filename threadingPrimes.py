from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from os import walk

import time
import traceback, sys


class WorkerSignals(QObject):
    '''
    Defines the signals available from a running worker thread.

    Supported signals are:

    finished
        No data

    error
        tuple (exctype, value, traceback.format_exc() )

    result
        object data returned from processing, anything

    progress
        int indicating % progress

    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)
    progress = pyqtSignal(int)


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super(Worker, self).__init__()

        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

        # Add the callback to our kwargs
        self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.fn(*self.args, **self.kwargs)
        except:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)  # Return the result of the processing
        finally:
            self.signals.finished.emit()  # Done



class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.counter = 0
        self.threadCount = 0
        self.threadAmount = 0
        self.files = next(walk("./rand_files"), (None, None, []))[2]  # [] if no file
        print("Files: %d" % len(self.files))
        self.files_done = 0
        self.max_primary_number = 0
        self.min_primary_number = 100000000000000

        layout = QVBoxLayout()

        self.l = QLabel("Time passed: 0")
        self.l_threads = QLabel("Threads: 0")
        self.l_files_done = QLabel("Files done: 0")
        self.l_max_primary_number = QLabel("Max primary number: 0")
        self.l_min_primary_number = QLabel("Min primary number: 0")
        a = QPushButton("Add")
        a.pressed.connect(self.thread_increase)
        b = QPushButton("Remove")
        b.pressed.connect(self.thread_remove)

        layout.addWidget(self.l)
        layout.addWidget(self.l_threads)
        layout.addWidget(self.l_files_done)
        layout.addWidget(self.l_max_primary_number)
        layout.addWidget(self.l_min_primary_number)
        layout.addWidget(a)
        layout.addWidget(b)

        w = QWidget()
        w.setLayout(layout)

        self.setCentralWidget(w)

        self.show()

        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.recurring_timer)
        self.timer.start()

    def progress_fn(self, n):
        print("%d%% done" % n)

    def execute_this_fn(self, progress_callback):
        if (len(self.files) > 0):
            current_file = self.files[len(self.files) - 1]
            self.files.pop()
            print("Current file: %s" % current_file)
            lines = []
            with open('./rand_files/%s' % current_file) as f:
                lines = f.readlines()
                count = 0
                for line in lines:
                    count += 1
                    num = int(line)
                    # define a flag variable
                    flag = False

                    # prime numbers are greater than 1 and make sense to be checked
                    if (num > 1 and (num > self.max_primary_number or num < self.min_primary_number)):
                        # check for factors
                        for i in range(2, num):
                            if (num % i) == 0:
                                # if factor is found, set flag to True
                                flag = True
                                # break out of loop
                                break

                    # check if flag is True
                    if flag:
                        print(num, "is not a prime number")
                    else:
                        if(num > self.max_primary_number):
                            self.max_primary_number = num
                            self.l_max_primary_number.setText("Max primary number: %d" % self.max_primary_number)
                        if(num < self.min_primary_number):
                            self.min_primary_number = num
                            self.l_min_primary_number.setText("Min primary number: %d" % self.min_primary_number)
                                        

        self.files_done += 1
        self.l_files_done.setText("Files done: %d" % self.files_done)
        return "Done."

    def print_output(self, s):
        print(s)

    def thread_complete(self):
        print("THREAD COMPLETE!")
        self.threadCount -= 1
        if(self.threadCount < self.threadAmount):
            self.thread_add()

    def thread_add(self):
        if(len(self.files) > 0):
            self.threadCount += 1
            self.oh_no()
            print("Adding thread")

    def thread_increase(self):
        if (self.threadAmount < self.threadpool.maxThreadCount()):
            self.threadAmount += 1
            print("Thread amount: %d" % self.threadAmount)
            self.l_threads.setText("Threads: %d" % self.threadAmount)
            self.thread_add()

    def thread_remove(self):
        if (self.threadAmount > 0):
            self.threadAmount -= 1
            print("Thread amount: %d" % self.threadAmount)
            self.l_threads.setText("Threads: %d" % self.threadAmount)

    def oh_no(self):
        # Pass the function to execute
        worker = Worker(self.execute_this_fn) # Any other args, kwargs are passed to the run function
        worker.signals.result.connect(self.print_output)
        worker.signals.finished.connect(self.thread_complete)
        worker.signals.progress.connect(self.progress_fn)

        # Execute
        self.threadpool.start(worker)


    def recurring_timer(self):
        self.counter +=1
        self.l.setText("Time passed: %d seconds" % self.counter)


app = QApplication([])
window = MainWindow()
app.exec_()