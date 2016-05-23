#! /usr/bin/python3

import av
import argparse
from parse import compile

def get_sec(t):
    return sum(int(x) * 60 ** i for i,x in enumerate(reversed(t.split(":"))))

def split_audio(file, names, times, **kwargs):
    container = av.open(file)
    stream = next(s for s in container.streams if s.type == 'audio')
    times = [get_sec(t) for t in times] + [stream.duration / stream.rate]
    for name, time, prev in zip(names, times[1:], times[:-1]):
        container.seek(float(prev), mode='time')
        running_time = prev * stream.rate
        output = av.open(name + ".m4a", "w")
        output_stream = output.add_stream(kwargs.get("codec") or "aac", stream.rate)
        for packet in container.demux(stream):
            running_time += packet.duration
            for frame in packet.decode():
                output_packet = output_stream.encode(frame)
                if output_packet:
                    output.mux(output_packet)
            if running_time > time * stream.rate:
                output.close()
                break

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("file", type=str,
                        help="Path to the audio file")
    parser.add_argument("-l", "--list", type=str,
                        help="Path to a list of songs and times. Defaults to ./list.txt")
    parser.add_argument("-c", "--codec", type=str,
                        help="The format to encode the split audio with. Use any of ffmpeg's supported formats (vorbis, aac, etc)")
    parser.add_argument("-f", "--format", type=str,
                        help="The format of the song list. If a line of the song list is, for example, 3. Lore - 23:10, one would format it as \"{dontcare}. {name} - {time}\". Only {name} and {time} have significance in the format string")

    args = parser.parse_args()
    with open(args.list or "list.txt") as list:
        lines = [line.rstrip('\n') for line in list]
        if args.format:
            parse_expression = compile(args.format)
        else:
            parse_expression = compile(lines[0])
            lines = lines[1:] # The first line of the list is the format string
        results = [parse_expression.parse(str(line)) for line in lines]
    names = [result['name'] for result in results]
    times = [result['time'] for result in results]
    split_audio(args.file, names, times, codec=args.codec)
