#
# compare_folder.py
# Copyright (C) 2015 Christophe Meneboeuf <xtof@xtof.info>
#
#  This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import hashlib
import os
from filecmp import dircmp


# PRINTING UNIQUE FILES IN EACH FOLDER
def find_unique_files(dcmp):
    uniqueFilesLeft = []
    uniqueFilesRight = []
    # dir1 unique files
    if len(dcmp.left_only) != 0:
        for filename in dcmp.left_only:
            uniqueFilesLeft.append(dcmp.left+"/"+filename)
    # dir2 unique files
    if len(dcmp.right_only) != 0:
        for filename in dcmp.right_only:
            uniqueFilesRight.append(dcmp.right+"/"+filename)
    # recursive call to process the sub folders
    for sub_dcmp in dcmp.subdirs.values():
        sub_uniques = find_unique_files(sub_dcmp)
        uniqueFilesLeft += sub_uniques["left"]
        uniqueFilesRight += sub_uniques["right"]
    uniqueFilesLeft.sort()
    uniqueFilesRight.sort()
    return {"left": uniqueFilesLeft, "right": uniqueFilesRight}


# BUILDING A LIST OF COMMON FILES' PATH INSIDE A FOLDER
def build_common_files(dcmp):
    # listing common files in dir
    commonFiles = []
    for filename in dcmp.common_files:
        commonFiles.append(dcmp.left + "/" + filename)
    # listing in sub-dirs
    for subdir in dcmp.common_dirs:
        subCommonFiles = build_common_files(dircmp(dcmp.left + "/" + subdir, dcmp.right + "/" + subdir))
        for filename in subCommonFiles:
            commonFiles.append(filename)
    commonFiles.sort()
    return commonFiles


# HASHING A FILE, READ BY 16M CHUNKS NOT TO OVERLOAD MEMORY
def hash_file(filepath):
    hasher = hashlib.sha1()
    with open(filepath, 'rb') as f:
        while True:
            buf = f.read(0x100000)
            if not buf:
                break
            hasher.update(buf)
    return hasher.hexdigest()


# PRINTING FILE LIST
def print_unique_files(files):
    if len(files) != 0:
        for filepath in files:
            if os.path.isdir(filepath):
                filepath += '/'
            print("unique: " + filepath)

# MAIN ==============================================
# parsing arguments
parser = argparse.ArgumentParser(description="Directories to compare.")
parser.add_argument("dir1")
parser.add_argument("dir2")
args = parser.parse_args()
if not os.path.isdir(args.dir1):
    print(args.dir1 + " is not a valid directory")
    exit(-1)
if not os.path.isdir(args.dir2):
    print(args.dir2 + " is not a valid directory")
    exit(-1)

# Rough analyse of the two directories
print("Analyzing directories...")
dcmp = dircmp(args.dir1, args.dir2)
uniqueFiles = find_unique_files(dcmp)

# build a common files list
print("Building common files list...")
commonFiles = build_common_files(dcmp)
relativePathsCommonFiles = []
for filename in commonFiles:  # removing the root folder
    relativePathsCommonFiles.append(filename[len(args.dir1)+1:])

# Finding and displaying files that are differents
filesDifferent = []
print("Searching for file differences by computing hashes...\n")
for filepath in relativePathsCommonFiles:
    filepathLeft = args.dir1 + "/" + filepath
    hashLeft = hash_file(filepathLeft)
    filepathRight = args.dir2 + "/" + filepath
    hashRight = hash_file(filepathRight)
    if hashLeft != hashRight:
        stringLeft = filepathLeft + "\t\t\tsha1: " + hashLeft
        stringRight = filepathRight + "\t\t\tsha1: " + hashRight
        filesDifferent.append([filepathLeft, filepathRight])
        print(stringLeft)
        print(stringRight)

# printing unique files
print_unique_files(uniqueFiles["left"])
print_unique_files(uniqueFiles["right"])

if len(filesDifferent)+len(uniqueFiles["left"])+len(uniqueFiles["right"]) == 0:
    print("NO DIFFERENCE FOUND :)\n")
