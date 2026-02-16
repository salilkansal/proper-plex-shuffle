import os
import shutil

source_folder = r'D:\Media\Movies'

for filename in os.listdir(source_folder):
    if filename.endswith('.mkv'):
        movie_name = os.path.splitext(filename)[0]
        movie_folder = os.path.join(source_folder, movie_name)

        if not os.path.exists(movie_folder):
            # print(f"Will create folder: {movie_folder}")
            os.mkdir(movie_folder)

        movie_file = os.path.join(source_folder, filename)
        destination = os.path.join(movie_folder, filename)

        shutil.move(movie_file, destination)
        # print(f"Will move file {movie_file} to {destination} folder")
